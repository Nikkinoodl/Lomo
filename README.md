# Lomo
A GIMP script that emulates the classic look of Diana and Holga camera images.

This plugin is based on the work of others including https://elsamuko.github.io/gimp-elsamuko/scripts/lomo.html and updates the scripts to work in GIMP 2.10. It has been converted to Python and updated to work in Gimp 3.0

The Gimp 3.0 version contains a re-usable workaround that enables the Gimp.Drawable.curves_spline method to be used in non-linear space.

The plugin allows the optional application of multiple effects from a single dialog, including: wide angle distortion, lens blur, focus blur, grain, overexposure, and sharpness. Contrast and saturation can also be changed. However, the true benefit of this plugin is to allow the application of an assortment of color effects, many of which are complex to perform manually and difficult to repeat accurately.

The XPro Green effect seen in the image below involves appying different curve splines to each of the red, green and blue channels in non-linear color space.

![XPro green effect applied to an industrial street scene](https://github.com/Nikkinoodl/Lomo/assets/17559271/922410dc-fc20-43a0-90b1-998d58269156)

The XPro LAB effect seen in the next image involves decomposing the image into LAB channels. The A and B channels individually undergo a levels stretch in linear space  followed by a gamma correction, before being recomposed back into the original image.

![XPro LAB effect applied to a wooded scene](https://github.com/user-attachments/assets/060e5102-36f4-4207-a598-1eb906b76022)

The Payne's Gray black and white effect is used together with lens distortion, focus blur, grain, and overexposure to get the Holga Camera effect seen in the next image.

![Paynes gray effect and wide angle distortion applied to a Stamford, Connecticut street scene](https://github.com/user-attachments/assets/09e4429a-8183-4144-a991-f4277ec4d487)

To install, download the file and place it in the appropriate folder location. You can find this by selecting Edit/Preferences then navigating to Folder->Scripts (for the Gimp 2.10 script) or Folder->Plugins (for the Gimp 3.0 plugin) from the GIMP menu. If you have not already done do, it is much easier to find these folders if you make them visible — in Windows, you can do this from the menu bar in File Explorer.

Install the GIMP 2 script directly in the script folder. Note that the GIMP 3 plugin must be installed inside a sub-folder with the same name as the plugin. The installation location will looks something like those shown below.

Windows:

```

C:\user\<username>\AppData\Roaming\GIMP\2.10\scripts
C:\user\<username>\AppData\Roaming\GIMP\3.0\plugins\gimp_lomo\gimp_lomo.py

```

Linux:

```

/usr/<username>/.config/GIMP/2.10/scripts
/usr/<username>/.config/GIMP/3.0/plugins/gimp_lomo/gimp_lomo.py

```

And that's all there is to it. Open GIMP and you're now ready to go with your new plugin.
