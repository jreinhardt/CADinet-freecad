CADinet-FreeCAD
===============

[CADinet](https://github.com/jreinhardt/CADinet) is a web application that
allows to upload 3D models via a REST API for publishing on the web and in the
[thingtracker network](https://thingtracker.net).

CADinet-FreeCAD is a FreeCAD macro that uses this API to provide 1-click upload
and publishing of parts from FreeCAD.

Attention: This is an early experimentation and everything is in flow and might
break at any point in time. Don't use CADinet as the sole place to store your
models. Use at your own risk.

License
-------

CADinet-FreeCAD is published under the [MIT license](http://opensource.org/licenses/MIT).


How to setup
------------

First you need to register an account with a CADinet. If you can not find an
instance that allows registrations, you can always run your own. For a detailed
description see [here](https://github.com/jreinhardt/CADinet). From the
registration you get a username and a random password. Write them down, we will
need them later. If you loose these credentials, your account on the CADinet is
lost.

Next we need to install the FreeCAD macro. Download the [`cadinet.FCMacro`](https://raw.githubusercontent.com/jreinhardt/CADinet-freecad/master/cadinet.FCMacro) file
from the CADinet-FreeCAD repository and place it in your macro directory. If
you are unsure where your macro directory is located, you can look it up in
FreeCAD under Preferences in the Macros tab under Macro Path. Copy the file
there.

Now edit the file with a text editor. At the beginning there is a section with
configuration variables. Substitute your username and password, and the url of
the CADinet you registered with.

If you want you can setup a [toolbar button](http://freecadweb.org/wiki/index.php?title=Macros_recipes#How_to_use.3F)

That's it!

How to use
----------

Open a model that you want to upload to the CADinet. You can enter a
descriptive comment for the model by opening the Project information in the
file menu.

Note that CADinet only accepts models licenced under certain licenses, to avoid
legal difficulties with the hosting and distribution of uploaded models.

Then execute the cadinet macro using the Macro menu. Depending on the
complexity of the model and your internet connection it might take a while but
afterwards, your model should appear on the CADinet.
