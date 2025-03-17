#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BSTEMPER命令解析器测试脚本
"""

from typing import List, Dict, Any
import os
import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径，以便导入模块
sys.path.append(str(Path(__file__).parent.parent))
# 导入MCT解析器
from mct_parser import MCTParser, MCTModel

def test_bstemper_parsing():
    """测试BSTEMPER命令解析"""
    # 创建测试MCT数据
    test_mct_content = """
*VERSION
MIDAS CIVIL 2018(v1.1)

*UNIT
N, mm, KJ, C

*BSTEMPER    ; Beam Section Temperature
; ELEM_LIST, DIR, REF, NUM, GROUP, bPSC              ; line 1
;   TYPE1, ELAST1, THERMAL1, B1, H11, T11, H21, T21  ; line 2
  1, LZ, Top, 3, , NO
    INPUT,  3.55e+07, 1e-05,  20.1,  0, 14,  0.1, 5.5
    INPUT,  3.55e+07, 1e-05,  20.1,  0.1, 5.5,  0.28, 2.2
    INPUT,  3.55e+07, 1e-05,  9.525,  0.28, 2.2,  0.4, 0
  2, LZ, Top, 3, , NO
    INPUT,  3.55e+07, 1e-05,  20.1,  0, 14,  0.1, 5.5
    INPUT,  3.55e+07, 1e-05,  20.1,  0.1, 5.5,  0.28, 2.2
    INPUT,  3.55e+07, 1e-05,  9.525,  0.28, 2.2,  0.4, 0
  3, LZ, Top, 3, , NO
    INPUT,  3.55e+07, 1e-05,  20.1,  0, 14,  0.1, 5.5
    INPUT,  3.55e+07, 1e-05,  20.1,  0.1, 5.5,  0.28, 2.2
    INPUT,  3.55e+07, 1e-05,  9.525,  0.28, 2.2,  0.4, 0
"""

    # 保存到临时文件
    temp_file = "temp_bstemper_test.mct"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(test_mct_content)
    
    try:
        # 解析MCT文件
        parser = MCTParser()
        model = parser.parse_file(temp_file)
        
        # 检查是否有解析错误
        if model.errors:
            print("解析错误:")
            for error in model.errors:
                print(f"  - {error}")
            return False
        
        # 获取BSTEMPER命令
        bstemper_data = model.get_command("BSTEMPER")
        if not bstemper_data:
            print("未找到BSTEMPER命令")
            return False
        
        # 打印温度数据
        print("\nBSTEMPER命令解析结果:")
        print(f"共有 {len(bstemper_data.temperatures)} 个梁温度定义")
        
        for i, temp_data in enumerate(bstemper_data.temperatures):
            print(f"\n温度定义 #{i+1}:")
            print(f"  元素ID: {temp_data['elem_id']}")
            print(f"  方向: {temp_data['direction']}")
            print(f"  参考点: {temp_data['ref_point']}")
            print(f"  截面数量: {temp_data['num_sections']}")
            print(f"  组名: {temp_data['group'] or '(无)'}")
            print(f"  是否PSC: {temp_data['is_psc']}")
            
            print(f"  截面数据:")
            for j, section in enumerate(temp_data['sections']):
                print(f"    截面 #{j+1}:")
                print(f"      弹性模量: {section['elasticity']}")
                print(f"      热膨胀系数: {section['thermal']}")
                print(f"      宽度: {section['width']}")
                print(f"      高度1: {section['h1']}")
                print(f"      温度1: {section['t1']}")
                print(f"      高度2: {section['h2']}")
                print(f"      温度2: {section['t2']}")
        
        return True
        
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)

def test_real_mct_file(file_path):
    """使用实际MCT文件测试BSTEMPER解析"""
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return False
    
    try:
        # 解析MCT文件
        parser = MCTParser()
        model = parser.parse_file(file_path)
        
        # 检查是否有解析错误
        if model.errors:
            print("\n解析错误:")
            for error in model.errors:
                print(f"  - {error}")
            print("\n")
            
        # 获取BSTEMPER命令
        bstemper_data = model.get_command("BSTEMPER")
        if not bstemper_data:
            print("未找到BSTEMPER命令")
            return False
        
        # 打印温度数据摘要
        print("\nBSTEMPER命令解析结果摘要:")
        print(f"共有 {len(bstemper_data.temperatures)} 个梁温度定义")
        
        # 只打印前3个元素的信息作为摘要
        for i, temp_data in enumerate(bstemper_data.temperatures[:3]):
            print(f"\n温度定义 #{i+1}:")
            print(f"  元素ID: {temp_data['elem_id']}")
            print(f"  方向: {temp_data['direction']}")
            print(f"  参考点: {temp_data['ref_point']}")
            print(f"  截面数量: {temp_data['num_sections']}")
            print(f"  组名: {temp_data['group'] or '(无)'}")
            print(f"  是否PSC: {temp_data['is_psc']}")
            print(f"  截面数量: {len(temp_data['sections'])}")
        
        if len(bstemper_data.temperatures) > 3:
            print(f"\n... 共 {len(bstemper_data.temperatures)} 个定义，仅显示前3个 ...")
        
        return True
        
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("===== 测试BSTEMPER命令解析器 =====")
    
    print("\n测试1: 解析示例MCT数据")
    result1 = test_bstemper_parsing()
    print(f"测试1结果: {'成功' if result1 else '失败'}")
    
    # 测试实际文件如果提供
    if len(sys.argv) > 1:
        real_file = sys.argv[1]
        print(f"\n测试2: 解析实际MCT文件 ({real_file})")
        result2 = test_real_mct_file(real_file)
        print(f"测试2结果: {'成功' if result2 else '失败'}")
    else:
        print("\n若要测试实际MCT文件，请提供文件路径作为命令行参数")
