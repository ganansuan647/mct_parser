"""
增强版MCT解析器基础模型

提供更灵活的扩展机制和更好的命令支持
"""

from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class MCTCommand(Enum):
    """MCT文件命令类型枚举，扩展支持更多命令"""
    # 基本命令
    VERSION = "VERSION"
    UNIT = "UNIT"
    PROJINFO = "PROJINFO"
    STRUCTYPE = "STRUCTYPE"
    ENDDATA = "ENDDATA"
    
    # 网格与节点
    NODE = "NODE"
    GRIDLINE = "GRIDLINE"
    
    # 单元定义
    ELEMENT = "ELEMENT"
    
    # 组定义
    GROUP = "GROUP"
    BNDR_GROUP = "BNDR-GROUP"
    LOAD_GROUP = "LOAD-GROUP"
    
    # 材料定义
    MATERIAL = "MATERIAL"
    MATL_COLOR = "MATL-COLOR"
    REBAR_MATL_CODE = "REBAR-MATL-CODE"
    
    # 时间依存材料属性
    TDM_FUNC = "TDM-FUNC"
    TDM_TYPE = "TDM-TYPE"
    TDM_ELAST = "TDM-ELAST"
    TDM_LINK = "TDM-LINK"
    ELEM_DEPMATL = "ELEM-DEPMATL"
    
    # 截面定义
    SECTION = "SECTION"
    SECT_COLOR = "SECT-COLOR"
    SECT_PSCVALUE = "SECT-PSCVALUE"
    DGN_SECT = "DGN-SECT"
    DGN_SECT_PSCVALUE = "DGN-SECT-PSCVALUE"
    COMP_GEN_SECT_PSC_DESIGN = "COMP-GEN-SECT-PSC-DESIGN"
    
    # 变截面组 - 新增支持
    TS_GROUP = "TS-GROUP"
    
    # 连接单元
    ELASTICLINK = "ELASTICLINK"
    RIGIDLINK = "RIGIDLINK"
    VLINK = "VLINK"
    FRICTION = "FRICTION"
    
    # 边界条件
    CONSTRAINT = "CONSTRAINT"
    SPRING = "SPRING"
    
    # 荷载定义
    STLDCASE = "STLDCASE"
    USE_STLD = "USE-STLD"
    SELFWEIGHT = "SELFWEIGHT"
    SYSTEMPER = "SYSTEMPER"
    BSTEMPER = "BSTEMPER"
    BEAMLOAD = "BEAMLOAD"
    CONLOAD = "CONLOAD"
    PRESSURE = "PRESSURE"
    PRESTRESS = "PRESTRESS"
    EFF_WIDTH = "EFF-WIDTH"
    LOADTOMASS = "LOADTOMASS"
    
    # 荷载组合
    LOADCOMB = "LOADCOMB"
    
    # 施工阶段
    LOAD_SEQ = "LOAD-SEQ"
    STAGE_CTRL = "STAGE-CTRL"
    
    # 分析控制
    EIGEN_CTRL = "EIGEN-CTRL"
    SPEC_CTRL = "SPEC-CTRL"
    MOVE_CTRL = "MOVE-CTRL"
    NONL_CTRL = "NONL-CTRL"
    
    # 水化热分析
    HYD_STAGE = "HYD-STAGE"
    HYD_CTRL = "HYD-CTRL"
    HYD_HEATSRC = "HYD-HEATSRC"
    
    # 其他命令
    CUTLINE = "CUTLINE"


class MCTBaseModel(BaseModel):
    """MCT模型基类"""
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"  # 允许额外字段


class CommandData(MCTBaseModel):
    """命令数据基类"""
    raw_lines: List[str] = Field(default_factory=list)
    line_nums: List[int] = Field(default_factory=list)  # 存储原始行号，便于错误定位


class MCTModel:
    """增强版MCT模型类，支持更多命令和更灵活的扩展机制"""
    
    def __init__(self):
        """初始化MCT模型"""
        self.commands: Dict[str, CommandData] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.file_path: Optional[str] = None
        
    def add_command(self, command_name: str, command_data: CommandData):
        """添加命令数据到模型"""
        self.commands[command_name] = command_data
    
    def get_command(self, command_name: str) -> Optional[CommandData]:
        """
        获取指定命令数据
        
        Args:
            command_name: 命令名称
            
        Returns:
            命令数据对象或None（如果不存在）
        """
        return self.commands.get(command_name)
    
    def get_commands_by_type(self, command_type: str) -> Dict[str, CommandData]:
        """
        获取指定类型的所有命令数据
        
        Args:
            command_type: 命令类型前缀
            
        Returns:
            以命令名为键，命令数据为值的字典
        """
        result = {}
        for cmd_name, cmd_data in self.commands.items():
            if cmd_name.startswith(command_type):
                result[cmd_name] = cmd_data
        return result
    
    def has_command(self, command_name: str) -> bool:
        """检查是否存在指定命令"""
        return command_name in self.commands
    
    def get_nodes(self) -> Dict:
        """获取所有节点"""
        if 'NODE' in self.commands:
            cmd_data = self.commands['NODE']
            # 处理字典形式的数据
            if isinstance(cmd_data, dict) and 'nodes' in cmd_data:
                return cmd_data['nodes']
            # 处理对象形式的数据
            elif hasattr(cmd_data, 'nodes'):
                return cmd_data.nodes
        return {}
    
    def get_elements(self) -> Dict:
        """获取所有单元"""
        if 'ELEMENT' in self.commands:
            cmd_data = self.commands['ELEMENT']
            # 处理字典形式的数据
            if isinstance(cmd_data, dict) and 'elements' in cmd_data:
                return cmd_data['elements']
            # 处理对象形式的数据
            elif hasattr(cmd_data, 'elements'):
                return cmd_data.elements
        return {}
    
    def get_materials(self) -> Dict:
        """获取所有材料"""
        if 'MATERIAL' in self.commands:
            cmd_data = self.commands['MATERIAL']
            # 处理字典形式的数据
            if isinstance(cmd_data, dict) and 'materials' in cmd_data:
                return cmd_data['materials']
            # 处理对象形式的数据
            elif hasattr(cmd_data, 'materials'):
                return cmd_data.materials
        return {}
    
    def get_sections(self) -> Dict:
        """获取所有截面"""
        if 'SECTION' in self.commands:
            cmd_data = self.commands['SECTION']
            # 处理字典形式的数据
            if isinstance(cmd_data, dict) and 'sections' in cmd_data:
                return cmd_data['sections']
            # 处理对象形式的数据
            elif hasattr(cmd_data, 'sections'):
                return cmd_data.sections
        return {}
    
    def get_tapered_section_groups(self) -> Dict:
        """获取所有变截面组"""
        result = {}
        # 获取TS-GROUP命令的数据
        ts_group_commands = self.get_commands_by_type('TS-GROUP')
        for cmd_name, cmd_data in ts_group_commands.items():
            # 处理字典形式的数据
            if isinstance(cmd_data, dict):
                result[cmd_name] = cmd_data
            # 处理对象形式的数据
            else:
                result[cmd_name] = cmd_data
        return result
    
    def get_elastic_links(self) -> Dict:
        """获取所有弹性连接单元"""
        if 'ELASTICLINK' in self.commands:
            cmd_data = self.commands['ELASTICLINK']
            # 处理字典形式的数据
            if isinstance(cmd_data, dict) and 'links' in cmd_data:
                return cmd_data['links']
            # 处理对象形式的数据
            elif hasattr(cmd_data, 'links'):
                return cmd_data.links
        return {}
    
    def validate(self) -> List[str]:
        """验证模型的完整性和一致性"""
        validation_errors = []
        
        # 检查必需的基本命令是否存在
        required_commands = [MCTCommand.VERSION.value, MCTCommand.UNIT.value]
        for cmd in required_commands:
            if cmd not in self.commands:
                validation_errors.append(f"缺少必需的命令: {cmd}")
        
        # 添加更多验证规则...
        
        return validation_errors
