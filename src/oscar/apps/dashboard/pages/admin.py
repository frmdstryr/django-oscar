from oscar.apps.dashboard.base import DashboardAdmin
from oscar.core.loading import get_model

FlatPage = get_model('flatpages', 'FlatPage')
PagePromotion = get_model('promotions', 'PagePromotion')
KeywordPromotion = get_model('promotions', 'KeywordPromotion')
RawHtmlPromotion = get_model('promotions', 'RawHTML')
ImagePromotion = get_model('promotions', 'Image')
MultiImagePromotion = get_model('promotions', 'MultiImage')
SingleProductPromotion = get_model('promotions', 'SingleProduct')
HandPickedProductListPromotion = get_model('promotions', 'HandPickedProductList')


class PagesAdmin(DashboardAdmin):
    model = FlatPage
    menu_label = 'Pages'
    menu_icon = 'map-o'
    dashboard_url = 'site-pages'
    list_display = ('title', 'url', 'is_active', 'menu')
    list_filter = ('is_active', 'menu')
    search_fields = ('title', 'content')


class PagePromotionAdmin(DashboardAdmin):
    model = PagePromotion
    menu_icon = 'file-text-o'


class KeywordPromotionAdmin(DashboardAdmin):
    model = KeywordPromotion
    menu_icon = 'search'
    menu_icon = 'file-word-o'


class HtmlPromotionAdmin(DashboardAdmin):
    model = RawHtmlPromotion
    menu_icon = 'file-code-o'


class ImagePromotionAdmin(DashboardAdmin):
    model = ImagePromotion
    menu_icon = 'file-image-o'


class MultiImagePromotionAdmin(DashboardAdmin):
    model = MultiImagePromotion
    menu_icon = 'image'


class SingleProductPromotionAdmin(DashboardAdmin):
    model = SingleProductPromotion
    menu_icon = 'file-pdf-o'


class HandPickedProductListPromotionAdmin(DashboardAdmin):
    model = HandPickedProductListPromotion
    menu_icon = 'file-archive-o'
