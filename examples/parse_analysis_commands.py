"""
分析控制命令解析示例

演示如何使用增强版MCT解析器解析分析控制命令
包括：EIGEN-CTRL, SPEC-CTRL, NONL-CTRL
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径，以便导入模块
sys.path.append(str(Path(__file__).parent.parent))

from mct_parser_enhanced.parsers.analysis_parsers import AnalysisParser
from mct_parser_enhanced.models.base import MCTModel


class MockParser:
    """模拟主解析器，用于示例"""
    
    def __init__(self):
        """初始化模拟解析器"""
        self.model = MCTModel()


def create_sample_data():
    """创建样例数据"""
    # 特征值分析控制数据
    eigen_ctrl_lines = [
        "EIGEN-CTRL",
        "10 100 1.0E-6 LANC 0.0 MASS 0"
    ]
    eigen_ctrl_line_nums = [1, 2]
    
    # 反应谱分析控制数据
    spec_ctrl_lines = [
        "SPEC-CTRL",
        "ABS 1 CQC DAMP 0.05 YES 30 0.01",
        "1.0 0.0 0.0",
        "0.0 1.0 0.0",
        "0.0 0.0 1.0"
    ]
    spec_ctrl_line_nums = [4, 5, 6, 7, 8]
    
    # 非线性分析控制数据
    nonl_ctrl_lines = [
        "NONL-CTRL",
        "STATI INCR 10 50 1.0E-4 1.0E-3 1.0E-3 ON ON AUTO 0.01"
    ]
    nonl_ctrl_line_nums = [10, 11]
    
    return {
        "eigen_ctrl": (eigen_ctrl_lines, eigen_ctrl_line_nums),
        "spec_ctrl": (spec_ctrl_lines, spec_ctrl_line_nums),
        "nonl_ctrl": (nonl_ctrl_lines, nonl_ctrl_line_nums)
    }


def main():
    """主函数"""
    print("开始分析控制命令解析示例")
    print("=" * 50)
    
    # 初始化模拟解析器和分析控制解析器
    mock_parser = MockParser()
    analysis_parser = AnalysisParser(mock_parser)
    
    # 创建示例数据
    sample_data = create_sample_data()
    
    print("解析特征值分析控制命令 (EIGEN-CTRL)...")
    eigen_ctrl_lines, eigen_ctrl_line_nums = sample_data["eigen_ctrl"]
    analysis_parser.parse_eigen_ctrl(eigen_ctrl_lines, eigen_ctrl_line_nums)
    
    print("解析反应谱分析控制命令 (SPEC-CTRL)...")
    spec_ctrl_lines, spec_ctrl_line_nums = sample_data["spec_ctrl"]
    analysis_parser.parse_spec_ctrl(spec_ctrl_lines, spec_ctrl_line_nums)
    
    print("解析非线性分析控制命令 (NONL-CTRL)...")
    nonl_ctrl_lines, nonl_ctrl_line_nums = sample_data["nonl_ctrl"]
    analysis_parser.parse_nonl_ctrl(nonl_ctrl_lines, nonl_ctrl_line_nums)
    
    # 解析完成，输出结果
    print("\n解析完成！\n")
    print("=" * 50)
    print("解析结果摘要:")
    print("=" * 50)
    
    # 输出特征值分析控制命令解析结果
    if mock_parser.model.has_command("EIGEN-CTRL"):
        eigen_ctrl = mock_parser.model.get_command("EIGEN-CTRL")
        print("\n特征值分析控制 (EIGEN-CTRL):")
        print(f"  - 模态数量: {eigen_ctrl.modes}")
        print(f"  - 最大迭代次数: {eigen_ctrl.max_iterations}")
        print(f"  - 收敛精度: {eigen_ctrl.tolerance}")
        print("  - 可选参数:")
        for k, v in eigen_ctrl.options.items():
            print(f"    - {k}: {v}")
    else:
        print("\n未找到特征值分析控制命令 (EIGEN-CTRL)")
    
    # 输出反应谱分析控制命令解析结果
    if mock_parser.model.has_command("SPEC-CTRL"):
        spec_ctrl = mock_parser.model.get_command("SPEC-CTRL")
        print("\n反应谱分析控制 (SPEC-CTRL):")
        print(f"  - 分析类型: {spec_ctrl.spec_type}")
        print(f"  - 工况ID: {spec_ctrl.case_id}")
        print(f"  - 组合方法: {spec_ctrl.comb_method}")
        print("  - 可选参数:")
        for k, v in spec_ctrl.options.items():
            print(f"    - {k}: {v}")
        print("  - 方向因子:")
        for i, factors in enumerate(spec_ctrl.direction_factors):
            print(f"    - 方向 {i+1}: {factors}")
    else:
        print("\n未找到反应谱分析控制命令 (SPEC-CTRL)")
    
    # 输出非线性分析控制命令解析结果
    if mock_parser.model.has_command("NONL-CTRL"):
        nonl_ctrl = mock_parser.model.get_command("NONL-CTRL")
        print("\n非线性分析控制 (NONL-CTRL):")
        print(f"  - 分析类型: {nonl_ctrl.analysis_type}")
        print(f"  - 非线性类型: {nonl_ctrl.nonl_type}")
        print(f"  - 荷载步数: {nonl_ctrl.load_steps}")
        print(f"  - 最大迭代次数: {nonl_ctrl.max_iterations}")
        print(f"  - 收敛容差: {nonl_ctrl.convergence_tol}")
        print(f"  - 位移容差: {nonl_ctrl.displacement_tol}")
        print(f"  - 力容差: {nonl_ctrl.force_tol}")
        print("  - 可选参数:")
        for k, v in nonl_ctrl.options.items():
            print(f"    - {k}: {v}")
    else:
        print("\n未找到非线性分析控制命令 (NONL-CTRL)")
    
    # 检查解析过程中的错误和警告
    if mock_parser.model.errors:
        print("\n解析错误:")
        for error in mock_parser.model.errors:
            print(f"  - {error}")
    
    if mock_parser.model.warnings:
        print("\n解析警告:")
        for warning in mock_parser.model.warnings:
            print(f"  - {warning}")
    
    print("\n" + "=" * 50)
    print("示例运行完成")


if __name__ == "__main__":
    main()
