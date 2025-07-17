#!/usr/bin/env python3
"""
插件结构检查脚本
"""

import os
import json
import yaml

def check_plugin_structure():
    """检查插件文件结构"""
    plugin_dir = "/home/nyz/AstrBot/data/plugins/astrbot_plugin_unikorn_news"
    
    required_files = [
        "main.py",
        "metadata.yaml", 
        "requirements.txt",
        "_conf_schema.json",
        "README.md"
    ]
    
    print("🔍 检查插件文件结构...")
    
    for file in required_files:
        file_path = os.path.join(plugin_dir, file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"❌ {file} - 缺失")
    
    # 检查metadata.yaml格式
    print("\n📋 检查metadata.yaml...")
    try:
        with open(os.path.join(plugin_dir, "metadata.yaml"), 'r', encoding='utf-8') as f:
            metadata = yaml.safe_load(f)
            required_keys = ['name', 'desc', 'version', 'author', 'repo']
            for key in required_keys:
                if key in metadata:
                    print(f"✅ {key}: {metadata[key]}")
                else:
                    print(f"❌ {key} - 缺失")
    except Exception as e:
        print(f"❌ metadata.yaml解析失败: {e}")
    
    # 检查配置schema
    print("\n⚙️ 检查配置schema...")
    try:
        with open(os.path.join(plugin_dir, "_conf_schema.json"), 'r', encoding='utf-8') as f:
            schema = json.load(f)
            print(f"✅ 配置项数量: {len(schema)}")
            for key in schema:
                print(f"  - {key}: {schema[key].get('type', 'unknown')}")
    except Exception as e:
        print(f"❌ 配置schema解析失败: {e}")
    
    # 检查requirements.txt
    print("\n📦 检查依赖包...")
    try:
        with open(os.path.join(plugin_dir, "requirements.txt"), 'r', encoding='utf-8') as f:
            deps = f.read().strip().split('\n')
            for dep in deps:
                if dep.strip():
                    print(f"✅ {dep.strip()}")
    except Exception as e:
        print(f"❌ requirements.txt读取失败: {e}")
    
    print("\n✨ 插件结构检查完成！")

if __name__ == "__main__":
    check_plugin_structure()
