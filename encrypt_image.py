
import base64
import io
import os
from pathlib import Path
from urllib.parse import unquote
from .core.core import get_sha256,dencrypt_image,dencrypt_image_v2,encrypt_image_v2
from PIL import PngImagePlugin,_util,ImagePalette
from PIL import Image as PILImage
from io import BytesIO
from typing import Optional
import sys

_password = '123qwe'

            
if PILImage.Image.__name__ != 'EncryptedImage':
    
    super_open = PILImage.open
    
    class EncryptedImage(PILImage.Image):
        __name__ = "EncryptedImage"
        @staticmethod
        def from_image(image:PILImage.Image):
            image = image.copy()
            img = EncryptedImage()
            img.im = image.im
            img.mode = image.mode
            img._size = image.size
            img.format = image.format
            if image.mode in ("P", "PA"):
                if image.palette:
                    img.palette = image.palette.copy()
                else:
                    img.palette = ImagePalette.ImagePalette()
            img.info = image.info.copy()
            return img
            
        def save(self, fp, format=None, **params):
            filename = ""
            if isinstance(fp, Path):
                filename = str(fp)
            elif _util.is_path(fp):
                filename = fp
            elif fp == sys.stdout:
                try:
                    fp = sys.stdout.buffer
                except AttributeError:
                    pass
            if not filename and hasattr(fp, "name") and _util.is_path(fp.name):
                # only set the name for metadata purposes
                filename = fp.name
            
            if not filename or not _password:
                # 如果没有密码或不保存到硬盘，直接保存
                super().save(fp, format = format, **params)
                return
            
            if 'Encrypt' in self.info and (self.info['Encrypt'] == 'pixel_shuffle' or self.info['Encrypt'] == 'pixel_shuffle_2'):
                super().save(fp, format = format, **params)
                return
            
            encrypt_image_v2(self, get_sha256(_password))
            self.format = PngImagePlugin.PngImageFile.format
            if self.info:
                self.info['Encrypt'] = 'pixel_shuffle_2'
            pnginfo = params.get('pnginfo', PngImagePlugin.PngInfo())
            pnginfo.add_text('Encrypt', 'pixel_shuffle_2')
            params.update(pnginfo=pnginfo)
            super().save(fp, format=self.format, **params)
            # 保存到文件后解密内存内的图片，让直接在内存内使用时图片正常
            dencrypt_image_v2(self, get_sha256(_password)) 
            if self.info:
                self.info['Encrypt'] = None
            
    def open(fp,*args, **kwargs):
        image = super_open(fp,*args, **kwargs)
        print(image.info.keys(),image.info.values())
        if _password and image.format.lower() == PngImagePlugin.PngImageFile.format.lower():
            pnginfo = image.info or {}
            if 'Encrypt' in pnginfo and pnginfo["Encrypt"] == 'pixel_shuffle':
                dencrypt_image(image, get_sha256(_password))
                pnginfo["Encrypt"] = None
                image = EncryptedImage.from_image(image=image)
                return image
            if 'Encrypt' in pnginfo and pnginfo["Encrypt"] == 'pixel_shuffle_2':
                dencrypt_image_v2(image, get_sha256(_password))
                pnginfo["Encrypt"] = None
                image = EncryptedImage.from_image(image=image)
                return image
        return EncryptedImage.from_image(image=image)

    # if _password:
    PILImage.Image = EncryptedImage
    PILImage.open = open
    
    print('图片加密插件加载成功')

# 这是一个节点，用于设置密码，即使不设置，也有默认密码 123qwe
class EncryptImage:
        
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "clip": ("CLIP",),
                "password":  ("STRING", {"default": "123qwe"}),
            }
        }
        
    RETURN_TYPES = ()
    FUNCTION = 'set_password'
    
    OUTPUT_NODE = True

    CATEGORY = "utils"
    
    def set_password(s,clip,password):
        global _password
        _password = password
        return ()
    
NODE_CLASS_MAPPINGS = {
    "EncryptImage": EncryptImage
}