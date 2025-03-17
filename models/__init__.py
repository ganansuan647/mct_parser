"""
增强版MCT解析器模型包
"""

from .base import MCTBaseModel, CommandData, MCTModel, MCTCommand
from .commands import (
    # 基本命令
    Version, Unit, ProjInfo, StructType,
    # 节点和单元
    Node, NodeCommand, Element, ElementCommand, ElementType,
    # 组定义
    Group, BndrGroup, LoadGroup,
    # 材料定义
    Material, MaterialCommand, MaterialType, MatlColor, TdmType, TdmElast, TdmLink, ElemDepmatl,
    # 截面定义
    Section, SectColor, SectPscvalue, DgnSect, DgnSectPscvalue, CompGenSectPscDesign,
    # 变截面组 - 新增支持
    TsGroup,
    # 连接单元
    ElasticLink, RigidLink, VLink, Friction,
    # 边界条件
    Constraint, Spring,
    # 荷载定义
    StldCase, UseStld, SelfWeight, SystemPer, BsTemper, BeamLoad, ConLoad, EffWidth, LoadToMass,
    # 荷载组合
    LoadComb,
    # 施工阶段
    LoadSeq, StageCtrl,
    # 分析控制
    EigenCtrl, SpecCtrl, NonlCtrl,
    # 水化热分析
    HydStage, HydCtrl, HydHeatsrc,
    # 其他命令
    CutLine
)

__all__ = [
    'MCTBaseModel', 'CommandData', 'MCTModel', 'MCTCommand',
    'Version', 'Unit', 'ProjInfo', 'StructType',
    'Node', 'NodeCommand', 'Element', 'ElementCommand', 'ElementType',
    'Group', 'BndrGroup', 'LoadGroup',
    'Material', 'MaterialCommand', 'MaterialType', 'MatlColor', 'TdmType', 'TdmElast', 'TdmLink', 'ElemDepmatl',
    'Section', 'SectColor', 'SectPscvalue', 'DgnSect', 'DgnSectPscvalue', 'CompGenSectPscDesign',
    'TsGroup',
    'ElasticLink', 'RigidLink', 'VLink', 'Friction',
    'Constraint', 'Spring',
    'StldCase', 'UseStld', 'SelfWeight', 'SystemPer', 'BsTemper', 'BeamLoad', 'ConLoad', 'EffWidth', 'LoadToMass',
    'LoadComb',
    'LoadSeq', 'StageCtrl',
    'EigenCtrl', 'SpecCtrl', 'NonlCtrl',
    'HydStage', 'HydCtrl', 'HydHeatsrc',
    'CutLine'
]
