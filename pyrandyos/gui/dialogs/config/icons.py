from pyrandyos.gui.icons.iconfont import IconSpec, IconLayer, IconStateSpec
from pyrandyos.gui.icons.thirdparty.codicons import Codicons
from pyrandyos.gui.icons.thirdparty.codicons import names as codicon_names

ConfigLayer = IconLayer(Codicons, codicon_names.json,
                        x=0, y=0.075, scale=0.5)
SaveLayer = IconLayer(Codicons, codicon_names.save, y=-0.075)
SaveConfigIcon = IconSpec(IconStateSpec([
    SaveLayer,
    ConfigLayer,
]))


HomeLayer = IconLayer(Codicons, codicon_names.home,
                      x=0, y=0.1, scale=0.5)
SaveLayer = IconLayer(Codicons, codicon_names.save, y=-0.075)
SaveLocalConfigIcon = IconSpec(IconStateSpec([
    SaveLayer,
    HomeLayer,
]))
