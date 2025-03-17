"""
分析控制解析器测试模块

测试EIGEN-CTRL、SPEC-CTRL和NONL-CTRL等命令的解析功能
"""

import sys
import unittest
from pathlib import Path

# 添加项目根目录到Python路径，以便导入模块
sys.path.append(str(Path(__file__).parent.parent))

from mct_parser_enhanced.parsers.analysis_parsers import AnalysisParser
from mct_parser_enhanced.models.base import MCTModel


class MockParser:
    """模拟主解析器，用于测试"""
    
    def __init__(self):
        """初始化模拟解析器"""
        self.model = MCTModel()


class TestAnalysisParserDirect(unittest.TestCase):
    """分析控制解析器直接测试类"""
    
    def setUp(self):
        """测试前初始化"""
        self.mock_parser = MockParser()
        self.analysis_parser = AnalysisParser(self.mock_parser)
    
    def test_eigen_ctrl_parsing(self):
        """测试特征值分析控制命令EIGEN-CTRL的解析"""
        # 创建测试数据
        test_lines = [
            "EIGEN-CTRL",
            "10 100 1.0E-6 LANC 0.0 MASS 0"
        ]
        test_line_nums = [1, 2]

        # 直接调用解析方法
        self.analysis_parser.parse_eigen_ctrl(test_lines, test_line_nums)
        
        # 验证解析结果
        self.assertTrue(self.mock_parser.model.has_command("EIGEN-CTRL"))
        eigen_ctrl = self.mock_parser.model.get_command("EIGEN-CTRL")
        
        # 验证基本参数
        self.assertEqual(eigen_ctrl.modes, 10)
        self.assertEqual(eigen_ctrl.max_iterations, 100)
        self.assertEqual(eigen_ctrl.tolerance, 1.0E-6)
        
        # 验证可选参数
        self.assertEqual(eigen_ctrl.options.get("method"), "LANC")
        self.assertEqual(eigen_ctrl.options.get("shift"), 0.0)
        self.assertEqual(eigen_ctrl.options.get("norm"), "MASS")
        self.assertEqual(eigen_ctrl.options.get("imass"), 0)
    
    def test_spec_ctrl_parsing(self):
        """测试反应谱分析控制命令SPEC-CTRL的解析"""
        # 创建测试数据
        test_lines = [
            "SPEC-CTRL",
            "ABS 1 CQC DAMP 0.05 YES 30 0.01",
            "1.0 0.0 0.0",
            "0.0 1.0 0.0",
            "0.0 0.0 1.0"
        ]
        test_line_nums = [1, 2, 3, 4, 5]

        # 直接调用解析方法
        self.analysis_parser.parse_spec_ctrl(test_lines, test_line_nums)
        
        # 验证解析结果
        self.assertTrue(self.mock_parser.model.has_command("SPEC-CTRL"))
        spec_ctrl = self.mock_parser.model.get_command("SPEC-CTRL")
        
        # 验证基本参数
        self.assertEqual(spec_ctrl.spec_type, "ABS")
        self.assertEqual(spec_ctrl.case_id, 1)
        self.assertEqual(spec_ctrl.comb_method, "CQC")
        
        # 验证可选参数
        self.assertEqual(spec_ctrl.options.get("damp_type"), "DAMP")
        self.assertEqual(spec_ctrl.options.get("damp_ratio"), 0.05)
        self.assertEqual(spec_ctrl.options.get("missing_mass"), "YES")
        self.assertEqual(spec_ctrl.options.get("cutoff_mode"), 30)
        self.assertEqual(spec_ctrl.options.get("cutoff_period"), 0.01)
        
        # 验证方向因子
        self.assertEqual(len(spec_ctrl.direction_factors), 3)
        self.assertEqual(spec_ctrl.direction_factors[0], [1.0, 0.0, 0.0])
        self.assertEqual(spec_ctrl.direction_factors[1], [0.0, 1.0, 0.0])
        self.assertEqual(spec_ctrl.direction_factors[2], [0.0, 0.0, 1.0])
    
    def test_nonl_ctrl_parsing(self):
        """测试非线性分析控制命令NONL-CTRL的解析"""
        # 创建测试数据
        test_lines = [
            "NONL-CTRL",
            "STATI INCR 10 50 1.0E-4 1.0E-3 1.0E-3 ON ON AUTO 0.01"
        ]
        test_line_nums = [1, 2]

        # 直接调用解析方法
        self.analysis_parser.parse_nonl_ctrl(test_lines, test_line_nums)
        
        # 验证解析结果
        self.assertTrue(self.mock_parser.model.has_command("NONL-CTRL"))
        nonl_ctrl = self.mock_parser.model.get_command("NONL-CTRL")
        
        # 验证基本参数
        self.assertEqual(nonl_ctrl.analysis_type, "STATI")
        self.assertEqual(nonl_ctrl.nonl_type, "INCR")
        self.assertEqual(nonl_ctrl.load_steps, 10)
        self.assertEqual(nonl_ctrl.max_iterations, 50)
        self.assertEqual(nonl_ctrl.convergence_tol, 1.0E-4)
        self.assertEqual(nonl_ctrl.displacement_tol, 1.0E-3)
        self.assertEqual(nonl_ctrl.force_tol, 1.0E-3)
        
        # 验证可选参数
        self.assertEqual(nonl_ctrl.options.get("line_search"), "ON")
        self.assertEqual(nonl_ctrl.options.get("large_disp"), "ON")
        self.assertEqual(nonl_ctrl.options.get("auto_time"), "AUTO")
        self.assertEqual(nonl_ctrl.options.get("time_step_min"), 0.01)
    
    def test_invalid_eigen_ctrl(self):
        """测试无效的EIGEN-CTRL命令"""
        # 创建测试数据 - 参数不足
        test_lines = [
            "EIGEN-CTRL",
            "10 100"
        ]
        test_line_nums = [1, 2]

        # 直接调用解析方法
        self.analysis_parser.parse_eigen_ctrl(test_lines, test_line_nums)
        
        # 验证解析结果 - 应生成错误
        self.assertFalse(self.mock_parser.model.has_command("EIGEN-CTRL"))
        self.assertTrue(any("无效的EIGEN-CTRL命令" in error for error in self.mock_parser.model.errors))


if __name__ == "__main__":
    unittest.main()
