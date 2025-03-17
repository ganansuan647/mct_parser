"""
测试ELASTICLINK解析器
"""
from typing import List, Dict, Any
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径，以便导入模块
sys.path.append(str(Path(__file__).parent.parent))

from mct_parser import MCTParser
from mct_parser.parsers.link_parsers import LinkParser

def test_elasticlink_parsing():
    """测试ELASTICLINK解析器"""
    # 创建一个测试文件
    test_content = """*ELASTICLINK    ; Elastic Link
; iNO, iNODE1, iNODE2, LINK, ANGLE, R_SDx, R_SDy, R_SDz, R_SRx, R_SRy, R_SRz, SDx, SDy, SDz, SRx, SRy, SRz ... 
;                      bSHEAR, DRy, DRz, GROUP                                                                  ; GEN
; iNO, iNODE1, iNODE2, LINK, ANGLE, bSHEAR, DRy, DRz, GROUP                                                     ; RIGID,SADDLE
; iNO, iNODE1, iNODE2, LINK, ANGLE, SDx, bSHEAR, DRy, DRz, GROUP                                                ; TENS,COMP
; iNO, iNODE1, iNODE2, LINK, ANGLE, DIR, FUNCTION, bSHEAR, DRENDI, GROUP                                        ; MULTI LINEAR
     1,   201,     2, RIGID,     0, NO, 0.5, 0.5, 支座
     2,     2,   202, RIGID,     0, NO, 0.5, 0.5, 支座
     3,   203,  2002, RIGID,     0, NO, 0.5, 0.5, 支座
"""
    
    test_file = "elasticlink_test.mct"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_content)
    
    try:
        # 解析测试文件
        parser = MCTParser()
        model = parser.parse_file(test_file)
        
        # 检查是否有解析错误
        if model.errors:
            print("解析错误:")
            for error in model.errors:
                print(f"  {error}")
        else:
            print("解析成功，没有错误")
        
        # 检查是否正确解析了ELASTICLINK命令
        if "ELASTICLINK" in model.commands:
            elasticlink = model.commands["ELASTICLINK"]
            print(f"\n成功解析ELASTICLINK，包含 {len(elasticlink.links)} 个链接")
            
            for link_id, link_data in elasticlink.links.items():
                print(f"\n链接 {link_id}:")
                print(f"  ID: {link_data['id']}")
                print(f"  主节点: {link_data['master_node']}")
                print(f"  从节点: {link_data['slave_node']}")
                print(f"  链接类型: {link_data['link_type']}")
                print(f"  角度: {link_data['angle']}")
                print(f"  选项: {link_data['options']}")
        else:
            print("\n未找到ELASTICLINK命令")
    
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    test_elasticlink_parsing()
