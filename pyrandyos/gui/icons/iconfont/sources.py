from pathlib import Path

from .fontspec import (
    IconCharMapFileSpec, IconFontGitCommit, IconFontSpec, IconTtfFileSpec,
)

QtAwesome = IconFontGitCommit(
    "https://github.com/spyder-ide/qtawesome",
    "b79946412c7ba58c739082634c8d67f99773cc4b",
    Path("LICENSE.txt")
)

Codicons_repo = IconFontGitCommit(
    "https://github.com/microsoft/vscode-codicons",
    "3f96711c6f617f419d1a84a4d86d92021fc7bda6",
    (Path("LICENSE"), Path("LICENSE-CODE"))
)

VSCode = IconFontGitCommit(
    "https://github.com/microsoft/vscode",
    "dfe124cea49046c8ad5d7902b3f05a60d27bc70b",
    Path("LICENSE.txt")
)

FluentUI_repo = IconFontGitCommit(
    "https://github.com/microsoft/fluentui-system-icons",
    "5baf88376599abf9914416c95d050c24c55f7000",
    Path("LICENSE")
)

qta_font_dir = Path("qtawesome/fonts")
fluent_font_dir = Path("fonts")


THIRDPARTY_FONTSPEC = {
    "Codicons": IconFontSpec(
        IconTtfFileSpec(VSCode, Path("src/vs/base/browser/ui/codicons/codicon/codicon.ttf"), "5608b14a69ae55c99a67ef20249a15c7"),  # noqa: E501
        IconCharMapFileSpec(Codicons_repo, Path("src/template/mapping.json"), 10, "8df7fbe29b47eff0917d6ecef17c5855"),  # noqa: E501
    ),
    "ElusiveIcons": IconFontSpec(
        IconTtfFileSpec(QtAwesome, qta_font_dir/"elusiveicons-webfont-2.0.ttf", "207966b04c032d5b873fd595a211582e"),  # noqa: E501
        IconCharMapFileSpec(QtAwesome, qta_font_dir/"elusiveicons-webfont-charmap-2.0.json", 16, "c3b93ddda4215b385290f85be52619ff"),  # noqa: E501
    ),
    "Fa5.Brands": IconFontSpec(
        IconTtfFileSpec(QtAwesome, qta_font_dir/"fontawesome5-brands-webfont-5.15.4.ttf", "513aa607d398efaccc559916c3431403"),  # noqa: E501
        IconCharMapFileSpec(QtAwesome, qta_font_dir/"fontawesome5-brands-webfont-charmap-5.15.4.json", 16, "5c56bff92bfdc668239f5acb9f3e9fdf")  # noqa: E501
    ),
    "Fa5": IconFontSpec(
        IconTtfFileSpec(QtAwesome, qta_font_dir/"fontawesome5-regular-webfont-5.15.4.ttf", "dc47e4089f5bcb25f241bdeb2de0fb58"),  # noqa: E501
        IconCharMapFileSpec(QtAwesome, qta_font_dir/"fontawesome5-regular-webfont-charmap-5.15.4.json", 16, "0c91f5f5feeaba3b1dfc825565258cee"),  # noqa: E501
    ),
    "Fa5.Solid": IconFontSpec(
        IconTtfFileSpec(QtAwesome, qta_font_dir/"fontawesome5-solid-webfont-5.15.4.ttf", "5de19800fc9ae73438c2e5c61d041b48"),  # noqa: E501
        IconCharMapFileSpec(QtAwesome, qta_font_dir/"fontawesome5-solid-webfont-charmap-5.15.4.json", 16, "e71dcf48ec1e03a2034ff38d94bc5aca"),  # noqa: E501
        solid=True,
    ),
    "Fa6.Brands": IconFontSpec(
        IconTtfFileSpec(QtAwesome, qta_font_dir/"fontawesome6-brands-webfont-6.7.2.ttf", "15d54d142da2f2d6f2e90ed1d55121af"),  # noqa: E501
        IconCharMapFileSpec(QtAwesome, qta_font_dir/"fontawesome6-brands-webfont-charmap-6.7.2.json", 16, "071f8106a165c7f69310d09d6802cd47"),  # noqa: E501
    ),
    "Fa6": IconFontSpec(
        IconTtfFileSpec(QtAwesome, qta_font_dir/"fontawesome6-regular-webfont-6.7.2.ttf", "2b9e6cb53822f6a9b42f15229a36811a"),  # noqa: E501
        IconCharMapFileSpec(QtAwesome, qta_font_dir/"fontawesome6-regular-webfont-charmap-6.7.2.json", 16, "2c6bc833abc45cdda3fe5c2249104771"),  # noqa: E501
    ),
    "Fa6.Solid": IconFontSpec(
        IconTtfFileSpec(QtAwesome, qta_font_dir/"fontawesome6-solid-webfont-6.7.2.ttf", "07312c769a05b2c17133da1a09db4ccf"),  # noqa: E501
        IconCharMapFileSpec(QtAwesome, qta_font_dir/"fontawesome6-solid-webfont-charmap-6.7.2.json", 16, "0677f8ff2f9ed4ef28ad421129508309"),  # noqa: E501
        solid=True,
    ),
    "FluentUI.Filled": IconFontSpec(
        IconTtfFileSpec(FluentUI_repo, fluent_font_dir/"FluentSystemIcons-Filled.ttf", "e3282e84d8d46e5024d6547c11b7900b"),  # noqa: E501
        IconCharMapFileSpec(FluentUI_repo, fluent_font_dir/"FluentSystemIcons-Filled.json", 10, "82a97b64b6e2af20f28155793dcb5a1c"),  # noqa: E501
    ),
    "FluentUI": IconFontSpec(
        IconTtfFileSpec(FluentUI_repo, fluent_font_dir/"FluentSystemIcons-Regular.ttf", "f3d8cc1d4f6435fe29d8c3b619047dec"),  # noqa: E501
        IconCharMapFileSpec(FluentUI_repo, fluent_font_dir/"FluentSystemIcons-Regular.json", 10, "0020dbda23979b4d876252f938c01e50"),  # noqa: E501
    ),
    "FluentUI.Light": IconFontSpec(
        IconTtfFileSpec(FluentUI_repo, fluent_font_dir/"FluentSystemIcons-Light.ttf", "d5c442567a0b0bdf068a96ebaba04748"),  # noqa: E501
        IconCharMapFileSpec(FluentUI_repo, fluent_font_dir/"FluentSystemIcons-Light.json", 10, "e9839f6ed1cf395e42f7725a0b4c1aab"),  # noqa: E501
    ),
    "FluentUI.Resize": IconFontSpec(
        IconTtfFileSpec(FluentUI_repo, fluent_font_dir/"FluentSystemIcons-Resizable.ttf", "b0897636fcc80e20b5dc5fd2283b268d"),  # noqa: E501
        IconCharMapFileSpec(FluentUI_repo, fluent_font_dir/"FluentSystemIcons-Resizable.json", 10, "6e53427d2b5efa09c0c1379a0f42b0a9"),  # noqa: E501
    ),
    "Material5": IconFontSpec(
        IconTtfFileSpec(QtAwesome, qta_font_dir/"materialdesignicons5-webfont-5.9.55.ttf", "b7d40e7ef80c1d4af6d94902af66e524"),  # noqa: E501
        IconCharMapFileSpec(QtAwesome, qta_font_dir/"materialdesignicons5-webfont-charmap-5.9.55.json", 16, "0e688abb70cf39c1661f4a25bd21d46c"),  # noqa: E501
    ),
    "Material6": IconFontSpec(
        IconTtfFileSpec(QtAwesome, qta_font_dir/"materialdesignicons6-webfont-6.9.96.ttf", "ecaabfbb23fdac4ddbaf897b97257a92"),  # noqa: E501
        IconCharMapFileSpec(QtAwesome, qta_font_dir/"materialdesignicons6-webfont-charmap-6.9.96.json", 16, "c458eb03521a472a03ffdfe942cfb0c0"),  # noqa: E501
    ),
    "Phosphor": IconFontSpec(
        IconTtfFileSpec(QtAwesome, qta_font_dir/"phosphor-1.3.0.ttf", "5b8dc57388b2d86243566b996cc3a789"),  # noqa: E501
        IconCharMapFileSpec(QtAwesome, qta_font_dir/"phosphor-charmap-1.3.0.json", 16, "186f14cc94722704983db710c552f591"),  # noqa: E501
    ),
    "RemixIcon": IconFontSpec(
        IconTtfFileSpec(QtAwesome, qta_font_dir/"remixicon-2.5.0.ttf", "888e61f04316f10bddfff7bee10c6dd0"),  # noqa: E501
        IconCharMapFileSpec(QtAwesome, qta_font_dir/"remixicon-charmap-2.5.0.json", 16, "a85177747108ccaa4095606913dd6584")  # noqa: E501
    ),
}
