"""
Smart Cloudinary storage.
Preserves file extension in the public_id so url() can determine resource_type.
"""
import os
import cloudinary
import cloudinary.uploader
from cloudinary_storage.storage import MediaCloudinaryStorage

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.m4v'}


def _resource_type_for(name):
    ext = os.path.splitext(name)[1].lower()
    if ext in IMAGE_EXTS:
        return 'image'
    if ext in VIDEO_EXTS:
        return 'video'
    return 'raw'


class SmartCloudinaryStorage(MediaCloudinaryStorage):

    def _upload(self, name, content):
        resource_type = _resource_type_for(name)
        options = {
            'use_filename': True,
            'unique_filename': True,
            'resource_type': resource_type,
            'tags': self.TAG,
            # Tell Cloudinary to keep the file extension in the public_id
            'format': os.path.splitext(name)[1].lstrip('.') or None,
        }
        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}
        folder = os.path.dirname(name)
        if folder:
            options['folder'] = folder
        return cloudinary.uploader.upload(content, **options)

    def _save(self, name, content):
        name = self._normalise_name(name)
        name = self._prepend_prefix(name)
        from django.core.files.uploadedfile import UploadedFile
        content = UploadedFile(content, name)
        response = self._upload(name, content)
        # Store public_id WITH extension so url() works correctly
        public_id = response['public_id']
        fmt = response.get('format', '')
        if fmt and not public_id.endswith('.' + fmt):
            public_id = public_id + '.' + fmt
        return public_id

    def url(self, name):
        name = self._prepend_prefix(name)
        resource_type = _resource_type_for(name)
        resource = cloudinary.CloudinaryResource(
            name, default_resource_type=resource_type
        )
        return resource.url
