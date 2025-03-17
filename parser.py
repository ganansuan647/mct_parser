"""
增强版MCT解析器核心模块
"""

import os
import re
from typing import Dict, List, Union, Optional, Any, Set, Tuple, Callable
from collections import defaultdict

from .models import (
    MCTCommand, MCTModel, CommandData,
    Version, Unit, ProjInfo, StructType,
    Node, NodeCommand, Element, ElementCommand, ElementType,
    Group, BndrGroup, LoadGroup,
    Material, MaterialCommand, MaterialType, MatlColor,
    TdmType, TdmElast, TdmLink, ElemDepmatl,
    Section, SectColor, SectPscvalue, DgnSect, DgnSectPscvalue, CompGenSectPscDesign,
    TsGroup,
    ElasticLink, RigidLink, VLink, Friction,
    Constraint, Spring,
    StldCase, UseStld, SelfWeight, SystemPer, BsTemper, BeamLoad, ConLoad, EffWidth, LoadToMass,
    LoadComb,
    LoadSeq, StageCtrl,
    EigenCtrl, SpecCtrl, NonlCtrl,
    HydStage, HydCtrl, HydHeatsrc,
    CutLine
)

# 导入解析器的具体实现子模块
from .parsers.basic_parsers import BasicCommandParser
from .parsers.node_element_parsers import NodeElementParser
from .parsers.material_parsers import MaterialParser
from .parsers.section_parsers import SectionParser
from .parsers.tapered_section_parsers import TaperedSectionParser
from .parsers.constraint_parsers import ConstraintParser
from .parsers.load_parsers import LoadParser
from .parsers.stage_parsers import StageParser
from .parsers.analysis_parsers import AnalysisParser
from .parsers.hydration_parsers import HydrationParser
from .parsers.link_parsers import LinkParser
from .parsers.constraint_parsers import ConstraintParser


class MCTParser:
    """
    增强版Midas Civil MCT文件解析器
    
    支持更多命令类型，包括变截面组、连接单元等
    采用插件式设计，便于扩展新的命令解析
    """
    
    def __init__(self):
        """初始化解析器"""
        self.model = MCTModel()
        self.raw_text = ""
        self.lines = []
        self.debug = False
        self.file_path = None
        
        # 初始化各类命令解析器
        self.basic_parser = BasicCommandParser(self)
        self.node_element_parser = NodeElementParser(self)
        self.material_parser = MaterialParser(self)
        self.section_parser = SectionParser(self)
        self.tapered_section_parser = TaperedSectionParser(self)
        self.constraint_parser = ConstraintParser(self)
        self.load_parser = LoadParser(self)
        self.stage_parser = StageParser(self)
        self.analysis_parser = AnalysisParser(self)
        self.hydration_parser = HydrationParser(self)
        self.link_parser = LinkParser(self)
        self.constraint_parser = ConstraintParser(self)
        
        # 初始化命令解析器映射
        self._init_command_parsers()
    
    def _init_command_parsers(self):
        """
        初始化命令解析器映射
        """
        # 命令解析器映射
        self.command_parsers = {
            # 基本命令
            MCTCommand.VERSION: self.basic_parser.parse_version,
            MCTCommand.UNIT: self.basic_parser.parse_unit,
            MCTCommand.PROJINFO: self.basic_parser.parse_projinfo,
            MCTCommand.STRUCTYPE: self.basic_parser.parse_structype,
            MCTCommand.ENDDATA: self.basic_parser.parse_enddata,
            
            # 节点和单元命令
            MCTCommand.NODE: self.node_element_parser.parse_node,
            MCTCommand.GRIDLINE: self.node_element_parser.parse_gridline,
            MCTCommand.ELEMENT: self.node_element_parser.parse_element,
            MCTCommand.GROUP: self.node_element_parser.parse_group,
            MCTCommand.BNDR_GROUP: self.node_element_parser.parse_bndr_group,
            MCTCommand.LOAD_GROUP: self.node_element_parser.parse_load_group,
            
            # 材料命令
            MCTCommand.MATERIAL: self.material_parser.parse_material,
            MCTCommand.MATL_COLOR: self.material_parser.parse_matl_color,
            MCTCommand.REBAR_MATL_CODE: self.material_parser.parse_rebar_matl_code,
            MCTCommand.TDM_FUNC: self.material_parser.parse_tdm_func,
            MCTCommand.TDM_TYPE: self.material_parser.parse_tdm_type,
            MCTCommand.TDM_ELAST: self.material_parser.parse_tdm_elast,
            MCTCommand.TDM_LINK: self.material_parser.parse_tdm_link,
            MCTCommand.ELEM_DEPMATL: self.material_parser.parse_elem_depmatl,
            
            # 截面命令
            MCTCommand.SECTION: self.section_parser.parse_section,
            MCTCommand.SECT_COLOR: self.section_parser.parse_sect_color,
            MCTCommand.SECT_PSCVALUE: self.section_parser.parse_sect_pscvalue,
            MCTCommand.DGN_SECT: self.section_parser.parse_dgn_sect,
            MCTCommand.DGN_SECT_PSCVALUE: self.section_parser.parse_dgn_sect_pscvalue,
            MCTCommand.COMP_GEN_SECT_PSC_DESIGN: self.section_parser.parse_comp_gen_sect_psc_design,
            
            # 变截面组命令
            MCTCommand.TS_GROUP: self.tapered_section_parser.parse_ts_group,
            
            # 连接单元命令
            MCTCommand.ELASTICLINK: self.link_parser.parse_elasticlink,
            MCTCommand.RIGIDLINK: self.link_parser.parse_rigidlink,
            MCTCommand.VLINK: self.link_parser.parse_vlink,
            MCTCommand.FRICTION: self.link_parser.parse_friction,
            
            # 边界条件命令
            MCTCommand.CONSTRAINT: self.constraint_parser.parse_constraint,
            MCTCommand.SPRING: self.constraint_parser.parse_spring,
            
            # 荷载命令
            MCTCommand.STLDCASE: self.load_parser.parse_stldcase,
            MCTCommand.USE_STLD: self.load_parser.parse_use_stld,
            MCTCommand.SELFWEIGHT: self.load_parser.parse_selfweight,
            MCTCommand.SYSTEMPER: self.load_parser.parse_systemper,
            MCTCommand.BSTEMPER: self.load_parser.parse_bstemper,
            MCTCommand.BEAMLOAD: self.load_parser.parse_beamload,
            MCTCommand.CONLOAD: self.load_parser.parse_conload,
            MCTCommand.PRESSURE: self.load_parser.parse_pressure,
            MCTCommand.PRESTRESS: self.load_parser.parse_prestress,
            MCTCommand.EFF_WIDTH: self.load_parser.parse_eff_width,
            MCTCommand.LOADTOMASS: self.load_parser.parse_loadtomass,
            MCTCommand.LOADCOMB: self.load_parser.parse_loadcomb,
            
            # 施工阶段命令
            MCTCommand.LOAD_SEQ: self.stage_parser.parse_load_seq,
            MCTCommand.STAGE_CTRL: self.stage_parser.parse_stage_ctrl,
            
            # 分析控制命令
            MCTCommand.EIGEN_CTRL: self.analysis_parser.parse_eigen_ctrl,
            MCTCommand.SPEC_CTRL: self.analysis_parser.parse_spec_ctrl,
            MCTCommand.MOVE_CTRL: self.analysis_parser.parse_move_ctrl,
            MCTCommand.NONL_CTRL: self.analysis_parser.parse_nonl_ctrl,
            
            # 水化热分析命令
            MCTCommand.HYD_STAGE: self.hydration_parser.parse_hyd_stage,
            MCTCommand.HYD_CTRL: self.hydration_parser.parse_hyd_ctrl,
            MCTCommand.HYD_HEATSRC: self.hydration_parser.parse_hyd_heatsrc,
            
            # 其他命令
            MCTCommand.CUTLINE: self.basic_parser.parse_cutline
        }
    
    def parse_file(self, file_path: str, debug: bool = False) -> MCTModel:
        """
        解析MCT文件
        
        Args:
            file_path: MCT文件路径
            debug: 是否输出调试信息
            
        Returns:
            解析后的MCT模型
        """
        self.file_path = file_path
        self.debug = debug
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 尝试多种编码，先尝试中文编码，最后尝试UTF-8
        encodings = ['gbk', 'gb2312', 'gb18030', 'big5', 'utf-8']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                if encoding == encodings[-1]:
                    raise UnicodeDecodeError(f"无法解码文件: {file_path}")
                continue
        
        return self.parse_text(text, debug)
    
    def parse_text(self, text: str, debug: bool = False) -> MCTModel:
        """
        解析MCT文本内容
        
        Args:
            text: MCT文本内容
            debug: 是否输出调试信息
            
        Returns:
            解析后的MCT模型
        """
        self.debug = debug
        self.raw_text = text
        self.lines = text.splitlines()
        self.model = MCTModel()
        
        # 分割命令块并解析
        command_blocks = self._split_command_blocks()
        
        # 解析每个命令块
        for cmd_name, (lines, line_nums) in command_blocks.items():
            # 尝试从字符串值获取枚举对象
            enum_cmd = None
            for enum_val in MCTCommand:
                if enum_val.value == cmd_name:
                    enum_cmd = enum_val
                    break
            
            # 首先尝试以枚举值为键
            if enum_cmd in self.command_parsers:
                try:
                    if self.debug:
                        print(f"解析命令(枚举): {cmd_name}")
                    self.command_parsers[enum_cmd](lines, line_nums)
                except Exception as e:
                    error_msg = f"解析命令 {cmd_name} 时出错: {str(e)}"
                    self.model.errors.append(error_msg)
            # 然后尝试以字符串值为键
            elif cmd_name in self.command_parsers:
                try:
                    if self.debug:
                        print(f"解析命令(字符串): {cmd_name}")
                    self.command_parsers[cmd_name](lines, line_nums)
                except Exception as e:
                    error_msg = f"解析命令 {cmd_name} 时出错: {str(e)}"
                    self.model.errors.append(error_msg)
            else:
                warning_msg = f"未知命令: {cmd_name}"
                if self.debug:
                    print(warning_msg)
                self.model.warnings.append(warning_msg)
        
        if self.debug:
            print(f"解析完成，共解析 {len(command_blocks)} 个命令块")
            if self.model.errors:
                print(f"错误: {len(self.model.errors)}")
                for err in self.model.errors:
                    print(f"  {err}")
            if self.model.warnings:
                print(f"警告: {len(self.model.warnings)}")
                for warn in self.model.warnings:
                    print(f"  {warn}")
        
        return self.model
    
    def _preprocess_line(self, line: str) -> str:
        """
        预处理一行内容，移除注释
        
        Args:
            line: 原始行内容
            
        Returns:
            处理后的行内容
        """
        # 移除注释 (分号后的内容)
        comment_index = line.find(';')
        if comment_index != -1:
            line = line[:comment_index].strip()
        else:
            line = line.strip()
        return line
    
    def _split_command_blocks(self) -> Dict[str, Tuple[List[str], List[int]]]:
        """
        分割文本为命令块
        
        Returns:
            命令名称到(行列表, 行号列表)的字典
        """
        command_blocks = {}
        current_cmd = None
        cmd_lines = []
        cmd_line_nums = []
        
        for i, line in enumerate(self.lines):
            line_num = i + 1
            line = self._preprocess_line(line)
            
            if not line:
                continue
            
            # 如果以*开头，认为是新命令的开始
            if line.startswith('*'):
                # 如果已有当前命令，则将其保存
                if current_cmd:
                    command_blocks[current_cmd] = (cmd_lines, cmd_line_nums)
                
                # 提取新命令名
                cmd_parts = line[1:].split()
                current_cmd = cmd_parts[0]
                cmd_lines = []
                cmd_line_nums = []
            
            # 添加当前行到当前命令
            if current_cmd:
                cmd_lines.append(line)
                cmd_line_nums.append(line_num)
        
        # 保存最后一个命令
        if current_cmd and cmd_lines:
            command_blocks[current_cmd] = (cmd_lines, cmd_line_nums)
        
        return command_blocks
    
    def _parse_index_list(self, text: str) -> List[int]:
        """
        解析索引列表表达式，支持以下格式:
        - 单个索引: 1
        - 索引列表: 1 2 3
        - 范围: 1to10
        - 范围步长: 1to10by2
        - 组合: 1 2 3to6 8to20by2
        
        Args:
            text: 索引列表表达式
            
        Returns:
            解析后的索引列表
        """
        result = []
        if not text or text.strip() == '':
            return result
        
        parts = text.split()
        for part in parts:
            if 'to' in part:
                range_parts = part.split('to')
                start = int(range_parts[0])
                
                if 'by' in range_parts[1]:
                    end_step = range_parts[1].split('by')
                    end = int(end_step[0])
                    step = int(end_step[1])
                else:
                    end = int(range_parts[1])
                    step = 1
                
                result.extend(list(range(start, end + 1, step)))
            else:
                try:
                    result.append(int(part))
                except ValueError:
                    pass  # 忽略非整数
        
        return result
