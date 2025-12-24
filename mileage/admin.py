from django.contrib import admin
from .models import MileageRecord
from .models import MileageImage
from django.utils.html import mark_safe


@admin.register(MileageImage)
class MileageImageAdmin(admin.ModelAdmin):
    list_display = ('record', 'thumbnail', 'uploaded_at')
    readonly_fields = ('thumbnail',)

    def thumbnail(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-width: 120px; max-height:80px;" />')
        return '-'
    thumbnail.short_description = 'Image'

@admin.register(MileageRecord)
class MileageAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'date', 'distance', 'status', 'preview')
    list_filter = ('status', 'date')
    readonly_fields = ('preview',)

    def preview(self, obj):
        # Show start_photo and first additional image as thumbnails
        imgs = []
        if obj.start_photo:
            imgs.append(obj.start_photo.url)
        first = obj.images.first()
        if first and first.image:
            imgs.append(first.image.url)

        if imgs:
            html = ''.join([f'<img src="{u}" style="max-width: 120px; max-height:80px; margin-right:4px;"/>' for u in imgs])
            return mark_safe(html)
        return '-'
    preview.short_description = 'Photos'
