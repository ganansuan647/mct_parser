"""
分析控制解析器模块

处理EIGEN-CTRL、SPEC-CTRL、NONL-CTRL等命令
"""

from typing import List

from ..models import (
    EigenCtrl, SpecCtrl, NonlCtrl
)


class AnalysisParser:
    """分析控制解析器类"""
    
    def __init__(self, parser):
        """
        初始化分析控制解析器
        
        Args:
            parser: 父解析器引用
        """
        self.parser = parser
    
    def parse_eigen_ctrl(self, lines: List[str], line_nums: List[int]):
        """
        解析EIGEN-CTRL命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        if len(lines) < 2:
            self.parser.model.errors.append("无效的EIGEN-CTRL命令: 缺少控制参数")
            return
        
        # 解析第一行的控制参数
        parts = lines[1].strip().split()
        
        # 至少需要3个参数：模态数量、最大迭代次数和精度
        if len(parts) < 3:
            self.parser.model.errors.append(f"无效的EIGEN-CTRL命令: 参数不足，行号 {line_nums[1]}")
            return
        
        try:
            modes = int(parts[0])
            max_iterations = int(parts[1])
            tolerance = float(parts[2])
            
            # 解析可选参数
            options = {}
            if len(parts) > 3:
                options['method'] = parts[3]
            if len(parts) > 4:
                options['shift'] = float(parts[4])
            if len(parts) > 5:
                options['norm'] = parts[5]
            if len(parts) > 6:
                options['imass'] = int(parts[6])
            
            eigen_ctrl_data = EigenCtrl(
                modes=modes,
                max_iterations=max_iterations,
                tolerance=tolerance,
                options=options,
                raw_lines=lines,
                line_nums=line_nums
            )
            
            self.parser.model.add_command("EIGEN-CTRL", eigen_ctrl_data)
        
        except ValueError as e:
            self.parser.model.errors.append(f"解析EIGEN-CTRL命令时出错: {str(e)}")
    
    def parse_spec_ctrl(self, lines: List[str], line_nums: List[int]):
        """
        解析SPEC-CTRL命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        if len(lines) < 2:
            self.parser.model.errors.append("无效的SPEC-CTRL命令: 缺少控制参数")
            return
        
        # 解析第一行的控制参数
        parts = lines[1].strip().split()
        
        # 至少需要3个参数：分析类型、工况ID和组合方法
        if len(parts) < 3:
            self.parser.model.errors.append(f"无效的SPEC-CTRL命令: 参数不足，行号 {line_nums[1]}")
            return
        
        try:
            spec_type = parts[0]
            case_id = int(parts[1])
            comb_method = parts[2]
            
            # 解析可选参数
            options = {}
            if len(parts) > 3:
                options['damp_type'] = parts[3]
            if len(parts) > 4:
                options['damp_ratio'] = float(parts[4])
            if len(parts) > 5:
                options['missing_mass'] = parts[5]
            if len(parts) > 6:
                options['cutoff_mode'] = int(parts[6])
            if len(parts) > 7:
                options['cutoff_period'] = float(parts[7])
            
            # 解析方向因子
            direction_factors = []
            for i in range(2, min(len(lines), 5)):  # 最多3行方向因子
                if i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("*"):
                    factor_parts = lines[i].strip().split()
                    factors = []
                    for part in factor_parts:
                        try:
                            factors.append(float(part))
                        except ValueError:
                            pass  # 忽略无效值
                    
                    if factors:
                        direction_factors.append(factors)
            
            spec_ctrl_data = SpecCtrl(
                spec_type=spec_type,
                case_id=case_id,
                comb_method=comb_method,
                options=options,
                direction_factors=direction_factors,
                raw_lines=lines,
                line_nums=line_nums
            )
            
            self.parser.model.add_command("SPEC-CTRL", spec_ctrl_data)
        
        except ValueError as e:
            self.parser.model.errors.append(f"解析SPEC-CTRL命令时出错: {str(e)}")
    
    def parse_move_ctrl(self, lines: List[str], line_nums: List[int]):
        """
        解析MOVE-CTRL命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        # 这里实现MOVE-CTRL命令的解析
        pass
    
    def parse_nonl_ctrl(self, lines: List[str], line_nums: List[int]):
        """
        解析NONL-CTRL命令
        
        Args:
            lines: 命令行列表
            line_nums: 行号列表
        """
        if len(lines) < 2:
            self.parser.model.errors.append("无效的NONL-CTRL命令: 缺少控制参数")
            return
        
        # 解析第一行的控制参数
        parts = lines[1].strip().split()
        
        # 至少需要7个参数
        if len(parts) < 7:
            self.parser.model.errors.append(f"无效的NONL-CTRL命令: 参数不足，行号 {line_nums[1]}")
            return
        
        try:
            analysis_type = parts[0]
            nonl_type = parts[1]
            load_steps = int(parts[2])
            max_iterations = int(parts[3])
            convergence_tol = float(parts[4])
            displacement_tol = float(parts[5])
            force_tol = float(parts[6])
            
            # 解析可选参数
            options = {}
            if len(parts) > 7:
                options['line_search'] = parts[7]
            if len(parts) > 8:
                options['large_disp'] = parts[8]
            if len(parts) > 9:
                options['auto_time'] = parts[9]
            if len(parts) > 10:
                options['time_step_min'] = float(parts[10])
            
            nonl_ctrl_data = NonlCtrl(
                analysis_type=analysis_type,
                nonl_type=nonl_type,
                load_steps=load_steps,
                max_iterations=max_iterations,
                convergence_tol=convergence_tol,
                displacement_tol=displacement_tol,
                force_tol=force_tol,
                options=options,
                raw_lines=lines,
                line_nums=line_nums
            )
            
            self.parser.model.add_command("NONL-CTRL", nonl_ctrl_data)
        
        except ValueError as e:
            self.parser.model.errors.append(f"解析NONL-CTRL命令时出错: {str(e)}")
