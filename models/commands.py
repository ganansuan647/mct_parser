"""
增强版MCT解析器命令模型

定义各种MCT命令的数据模型
"""

from enum import Enum
from typing import Dict, List, Union, Optional, Any, Set, Tuple, Callable
import numpy as np
from pydantic import BaseModel, Field, validator, root_validator

from .base import MCTBaseModel, CommandData


class Version(CommandData):
    """VERSION命令模型 - 版本信息"""
    version: str


class Unit(CommandData):
    """UNIT命令模型"""
    force: str
    length: str
    heat: str = ""
    temperature: str = ""


class ProjInfo(CommandData):
    """PROJINFO命令模型"""
    info: Dict[str, str] = Field(default_factory=dict)


class StructType(CommandData):
    """STRUCTYPE命令模型"""
    istruct_type: Union[int, str]
    imass: Union[int, str]
    ismas: Union[int, str]
    mass_offset: bool
    self_weight: bool
    gravity: Union[float, str]
    temperature: Union[float, str]
    align_beam: bool
    align_slab: bool
    rot_rigid: bool
    
    @validator('mass_offset', 'self_weight', 'align_beam', 'align_slab', 'rot_rigid', pre=True)
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.upper() == "YES"
        return v


class Node(MCTBaseModel):
    """节点数据模型"""
    id: int
    x: float
    y: float
    z: float
    
    def get_coords(self) -> np.ndarray:
        """获取节点坐标数组"""
        return np.array([self.x, self.y, self.z])


class NodeCommand(CommandData):
    """NODE命令模型"""
    nodes: Dict[int, Node] = Field(default_factory=dict)


class ElementType(str, Enum):
    """元素类型枚举"""
    BEAM = "BEAM"
    TRUSS = "TRUSS"
    TENSTR = "TENSTR"
    COMPTR = "COMPTR"
    CABLE = "CABLE"
    PLSOLID = "PLSOLID"
    PLATE = "PLATE"
    SHELL = "SHELL"
    SOLID = "SOLID"
    INTERFACE = "INTERFACE"
    ELASTICLINK = "ELASTICLINK"
    VLINK = "VLINK"
    FRICTION = "FRICTION"


class Element(MCTBaseModel):
    """元素基本数据模型"""
    id: int
    type: ElementType
    material: int
    property: int
    connectivity: List[int]  # 连接的节点
    angle: float = 0.0
    sub: int = 0
    extra_params: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('type', pre=True)
    def parse_element_type(cls, v):
        if isinstance(v, str):
            try:
                return ElementType(v)
            except ValueError:
                return v
        return v


class ElementCommand(CommandData):
    """ELEMENT命令模型"""
    elements: Dict[int, Element] = Field(default_factory=dict)


class Group(CommandData):
    """GROUP命令模型"""
    name: str
    node_list: List[int] = Field(default_factory=list)
    elem_list: List[int] = Field(default_factory=list)
    plane_type: Union[int, str] = 0


class BndrGroup(CommandData):
    """BNDR-GROUP命令模型"""
    name: str
    auto_type: Union[int, str] = 0


class LoadGroup(CommandData):
    """LOAD-GROUP命令模型"""
    names: List[str] = Field(default_factory=list)


class MaterialType(str, Enum):
    """材料类型枚举"""
    STEEL = "STEEL"
    CONC = "CONC"
    SRC = "SRC"
    USER = "USER"


class Material(MCTBaseModel):
    """材料基本数据模型"""
    id: int
    type: MaterialType
    name: str
    specific_heat: float = 0.0
    heat_coefficient: float = 0.0
    plastic: str = ""
    temperature_unit: str = "C"
    mass_considered: bool = False
    damping_ratio: float = 0.0
    properties: Dict[str, Any] = Field(default_factory=dict)


class MaterialCommand(CommandData):
    """MATERIAL命令模型"""
    materials: Dict[int, Material] = Field(default_factory=dict)


class MatlColor(CommandData):
    """MATL-COLOR命令模型"""
    colors: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


class TdmFunc(CommandData):
    """TDM-FUNC命令模型"""
    functions: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class TdmType(CommandData):
    """TDM-TYPE命令模型"""
    definitions: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class TdmElast(CommandData):
    """TDM-ELAST命令模型"""
    definitions: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class TdmLink(CommandData):
    """TDM-LINK命令模型"""
    links: Dict[int, Tuple[str, str]] = Field(default_factory=dict)


class ElemDepmatl(CommandData):
    """ELEM-DEPMATL命令模型"""
    properties: List[Tuple[List[int], str, float]] = Field(default_factory=list)


class Section(CommandData):
    """SECTION命令模型"""
    sections: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


class SectColor(CommandData):
    """SECT-COLOR命令模型"""
    colors: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


class SectPscvalue(CommandData):
    """SECT-PSCVALUE命令模型"""
    sections: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


class DgnSect(CommandData):
    """DGN-SECT命令模型"""
    sections: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


class DgnSectPscvalue(CommandData):
    """DGN-SECT-PSCVALUE命令模型"""
    sections: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


class CompGenSectPscDesign(CommandData):
    """COMP-GEN-SECT-PSC-DESIGN命令模型"""
    designs: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


# 新增的变截面组模型
class TsGroup(CommandData):
    """TS-GROUP命令模型 - 变截面组"""
    groups: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


# 连接单元命令模型
class ElasticLink(CommandData):
    """ELASTICLINK命令模型 - 弹性连接"""
    links: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


class RigidLink(CommandData):
    """RIGIDLINK命令模型 - 刚性连接"""
    links: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


class VLink(CommandData):
    """VLINK命令模型 - 虚拟连接"""
    links: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


class Friction(CommandData):
    """FRICTION命令模型 - 摩擦连接"""
    links: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


# 边界条件命令模型
class Constraint(CommandData):
    """CONSTRAINT命令模型 - 约束"""
    constraints: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


class Spring(CommandData):
    """SPRING命令模型 - 弹簧支撑"""
    springs: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


# 荷载定义命令模型
class StldCase(CommandData):
    """STLDCASE命令模型 - 静态荷载工况"""
    cases: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class UseStld(CommandData):
    """USE-STLD命令模型 - 使用静态荷载工况"""
    case_name: str


class SelfWeight(CommandData):
    """SELFWEIGHT命令模型 - 自重"""
    factors: Dict[str, float] = Field(default_factory=dict)


class SystemPer(CommandData):
    """SYSTEMPER命令模型 - 系统温度"""
    temperatures: Dict[str, float] = Field(default_factory=dict)


class BsTemper(CommandData):
    """
    BSTEMPER命令模型 - 梁截面温度
    
    格式:
    *BSTEMPER    ; Beam Section Temperature
    ; ELEM_LIST, DIR, REF, NUM, GROUP, bPSC              ; line 1
    ;   TYPE1, ELAST1, THERMAL1, B1, H11, T11, H21, T21  ; line 2
    ;   ...
    ;   TYPEn, ELASTn, THERMALn, Bn, H1n, T1n, H2n, T2n  ; line n+1
    ;   TYPE, ELAST, THERMAL, REF, BOPT, B, H1OPT, H1, H2OPT, H2, T1, T2 ; line 2(PSC)
    """
    temperatures: List[Dict[str, Any]] = Field(default_factory=list)


class BeamLoad(CommandData):
    """BEAMLOAD命令模型 - 梁荷载"""
    loads: List[Dict[str, Any]] = Field(default_factory=list)


class ConLoad(CommandData):
    """CONLOAD命令模型 - 节点荷载"""
    loads: List[Dict[str, Any]] = Field(default_factory=list)


class EffWidth(CommandData):
    """EFF-WIDTH命令模型 - 有效宽度因子"""
    factors: Dict[int, float] = Field(default_factory=dict)


class LoadToMass(CommandData):
    """LOADTOMASS命令模型 - 荷载转质量"""
    factors: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


# 荷载组合命令模型
class LoadComb(CommandData):
    """LOADCOMB命令模型 - 荷载组合"""
    combinations: Dict[str, float] = Field(default_factory=dict)


# 施工阶段命令模型
class LoadSeq(CommandData):
    """LOAD-SEQ命令模型 - 荷载顺序"""
    sequences: Dict[str, List[str]] = Field(default_factory=dict)


class StageCtrl(CommandData):
    """STAGE-CTRL命令模型 - 施工阶段控制"""
    settings: Dict[str, Any] = Field(default_factory=dict)


# 分析控制命令模型
class EigenCtrl(CommandData):
    """EIGEN-CTRL命令模型 - 特征值分析控制"""
    frequency: int = 0
    iterations: int = 20
    dimension: int = 0
    tolerance: float = 1e-6


class SpecCtrl(CommandData):
    """SPEC-CTRL命令模型 - 响应谱分析控制"""
    type: str = "SRSS"
    damping: float = 0.05
    add_sign: bool = False
    
    @validator('add_sign', pre=True)
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.upper() == "YES"
        return v


class NonlCtrl(CommandData):
    """NONL-CTRL命令模型 - 非线性分析控制"""
    method: str = "NEWTON"
    settings: Dict[str, Any] = Field(default_factory=dict)


# 水化热分析命令模型
class HydStage(CommandData):
    """HYD-STAGE命令模型 - 水化热施工阶段"""
    name: str
    steps: List[float] = Field(default_factory=list)
    active_elements: List[str] = Field(default_factory=list)
    active_boundaries: List[str] = Field(default_factory=list)
    deactive_boundaries: List[str] = Field(default_factory=list)


class HydCtrl(CommandData):
    """HYD-CTRL命令模型 - 水化热分析控制"""
    settings: Dict[str, Any] = Field(default_factory=dict)


class HydHeatsrc(CommandData):
    """HYD-HEATSRC命令模型 - 水化热源"""
    elements: Dict[List[int], str] = Field(default_factory=dict)


# 其他命令模型
class CutLine(CommandData):
    """CUTLINE命令模型 - 切线"""
    name: str
    direction: str
    point1: List[float]
    point2: List[float]
    color: List[int]

class ElementLink(CommandData):
    """ELEMENTLINK命令模型 - 单元连接"""
    point1: List[float]
    point2: List[float]
    color: List[int]
