"""
Конфигурация VK-бота.
"""

import os

VK_TOKEN: str = os.getenv("VK_TOKEN", "vk1.a.WfhUFdQ9Lcf8lbWZszV8sX5ltA_YPSljfet5rW9z4klIa1GEncORsXXvMTb2pRdnjS8v9Z8pIRG-78aPyjSHFN-k95wV8H-IVnvoduxDUQIeIPtS8W9r5n8qiM_9pcRohd078PdkxpAa-Alk61P1keXKF7KmeJ3jutqTW3CllbsyuU1orLw225_0MTkIc8o7Y8CFX2qbY3HYXm1uWeHTvg")

ADMIN_VK_ID: int = int(os.getenv("ADMIN_VK_ID", "436445091"))

GROUP_ID: int = int(os.getenv("GROUP_ID", "239389077"))
