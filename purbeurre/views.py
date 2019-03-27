from django.shortcuts import render, get_object_or_404
from django.views.generic import CreateView
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.core import signing
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from .forms import SearchForm, CustomUserCreationForm
from purbeurre.managers.openfoodfacts import ApiManager
from purbeurre.managers.database import DatabaseManager
from .models import ProductSubstituteProduct, Product


class GeneralView():
    @staticmethod
    def index(request):
        """render index page"""

        if request.method == "POST":
            navbar_search_form = SearchForm(request.POST, prefix="navbar")
            head_search_form = SearchForm(request.POST, prefix="head")
            valid = False
            search_post = None
            if navbar_search_form.is_valid():
                valid = True
                search_post = navbar_search_form.cleaned_data['search']
                head_search_form = SearchForm(prefix="head")
            elif head_search_form.is_valid():
                valid = True
                search_post = head_search_form.cleaned_data['search']
                navbar_search_form = SearchForm(prefix="navbar")
            if valid:
                products = ApiManager.do_research(search_post)
                return render(request, 'purbeurre/search.html', {
                    'search': search_post,
                    'products': products,
                    'navbar_search_form': navbar_search_form,
                })
        else:
            navbar_search_form = SearchForm(prefix="navbar")
            head_search_form = SearchForm(prefix="head")

        context = {
            'navbar_search_form': navbar_search_form,
            'head_search_form': head_search_form
        }

        return render(request, 'purbeurre/index.html', context)


    @staticmethod
    def show_credits(request):
        """render credits page"""

        return render(request, 'purbeurre/mentions_legales.html')


    @staticmethod
    def get_substitutes(request, bar_code):
        """ render substitutes page """

        navbar_search_form = SearchForm(prefix="navbar")
        sign = None
        sign_context = {'product': bar_code}
        substitutes_from_bdd = False

        product = ApiManager.get_product(bar_code)

        substitutes = DatabaseManager.get_substitutes_from_api(product)

        if not substitutes:
            substitutes = ApiManager.get_substitutes(product)
            if substitutes:
                DatabaseManager.save_substitutes(
                    product['categories_hierarchy'][-1],
                    substitutes)
        else:
            substitutes_from_bdd = True

        if substitutes_from_bdd:
            sign_context['substitutes'] = list(
                substitute.bar_code for substitute in substitutes)
            sign = signing.dumps(sign_context)
        elif substitutes:
            sign_context['substitutes'] = list(
                substitute['code'] for substitute in substitutes)
            sign = signing.dumps(sign_context)

        return render(request, 'purbeurre/substitutes.html', {
            'product': product,
            'substitutes': substitutes,
            'navbar_search_form': navbar_search_form,
            'sign': sign
        })


    @staticmethod
    def show_product(request, _id):
        """ render show product """

        product = get_object_or_404(Product.objects.prefetch_related('brands',
                                                                     'ingredients',
                                                                     'stores',
                                                                     'categories'),
                                    pk=_id)
        navbar_search_form = SearchForm(prefix="navbar")

        return render(request, 'purbeurre/show_product.html', {
            'product': product,
            'navbar_search_form': navbar_search_form,
        })


    @staticmethod
    @login_required
    def create_substitute_link(request, sign, substitute_bar_code):
        """ render the creating link beetween product """

        try:
            _dict = signing.loads(sign)
        except signing.BadSignature:
            raise Exception('Altération détectée !')

        if substitute_bar_code not in _dict['substitutes']:
            raise Exception('Mauvaise requête !')

        do_save = True
        do_save_p_s_p = True
        urllib_product = True
        urllib_substitute = True
        product, substitute = None, None

        try:
            product = Product.objects.get(bar_code=_dict['product'])
            urllib_product = False
        except Product.DoesNotExist:
            pass

        try:
            substitute = Product.objects.get(bar_code=substitute_bar_code)
            urllib_substitute = False
        except Product.DoesNotExist:
            pass

        if not urllib_product and not urllib_substitute:
            do_save = False

            p_s_p_db = ProductSubstituteProduct.objects.filter(
                users=request.user,
                from_product=product,
                to_product=substitute
            )

            if p_s_p_db.exists():
                do_save_p_s_p = False
                messages.success(request, 'Substitut déjà sauvergardé'
                                          ' pour ce produit !')

        if do_save or do_save_p_s_p:
            if do_save:
                if urllib_product:
                    product = ApiManager.get_product(_dict['product'])
                    if not product:
                        raise Exception('Produit non existant.')
                if urllib_substitute:
                    substitute = ApiManager.get_product(substitute_bar_code)
                    if not substitute:
                        raise Exception('Substitut non existant.')

                if (urllib_product and not urllib_substitute) or \
                        (not urllib_product and urllib_substitute):
                    if urllib_product and not urllib_substitute:
                        product = DatabaseManager.save_product(product)
                    else:
                        substitute = DatabaseManager.save_product(substitute)

                    DatabaseManager.save_link_p_s_p(request.user, product,
                                                    substitute)
                else:
                    DatabaseManager.save_product(product,
                                                 substitutes=(substitute,),
                                                 user=request.user)
            else:
                DatabaseManager.save_link_p_s_p(request.user, product, substitute)

            messages.success(request, 'Substitut sauvegardé !')

        navbar_search_form = SearchForm(prefix="navbar")

        return render(request, 'purbeurre/create_substitute_link.html', {
            'product': product,
            'substitute': substitute,
            'navbar_search_form': navbar_search_form
        })


    @staticmethod
    @login_required
    def show_user_link(request):
        """ render user link beetween openfoodfacts products """

        user_products = Product.objects.filter(from_product__users=request.user) \
            .prefetch_related('substitutes',
                              'substitutes__categories',
                              'substitutes__brands',
                              'substitutes__stores',
                              'substitutes__ingredients',
                              'brands',
                              'ingredients',
                              'stores',
                              'categories').distinct()

        paginator = Paginator(user_products, 4)

        page = request.GET.get('page')
        try:
            paginator = paginator.page(page)
        except PageNotAnInteger:
            paginator = paginator.page(1)
        except EmptyPage:
            paginator = paginator.page(paginator.num_pages)

        navbar_search_form = SearchForm(prefix="navbar")

        return render(request, 'purbeurre/show_user_link.html', {
            'liste': paginator,
            'navbar_search_form': navbar_search_form
        })


    @staticmethod
    @login_required
    def profile(request):
        """ render profile page """

        navbar_search_form = SearchForm(prefix="navbar")
        return render(request, 'purbeurre/profile.html', {
            'navbar_search_form': navbar_search_form
        })


class SignupView(CreateView):
    """ render signup page """

    form_class = CustomUserCreationForm
    success_url = '/'
    model = User

    def get_success_url(self):
        messages.success(self.request, 'Création de compte réussie !')
        return super(SignupView, self).get_success_url()


class CustomLoginView(SuccessMessageMixin, LoginView):
    """ render login page """

    success_message = "Vous êtes connecté !"
    redirect_authenticated_user = True
