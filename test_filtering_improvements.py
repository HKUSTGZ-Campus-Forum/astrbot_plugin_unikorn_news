#!/usr/bin/env python3
"""
测试改进后的筛选机制
"""

import re

def _is_button_text(text: str) -> bool:
    """判断文本是否为按钮文本（改进版）"""
    if not text or len(text.strip()) < 2:
        return True
        
    # 精确匹配的按钮文本模式（完全匹配）
    exact_button_patterns = [
        # 发帖相关
        r'^我要发帖$', r'^发布帖子$', r'^新建帖子$', r'^创建帖子$', r'^写帖子$', r'^发帖$',
        # 用户操作
        r'^登录$', r'^注册$', r'^退出$', r'^登出$', r'^注销$',
        # 导航按钮  
        r'^首页$', r'^主页$', r'^返回$', r'^上一页$', r'^下一页$', r'^末页$', r'^尾页$',
        # 分页相关
        r'^第\s*\d+\s*页$', r'^共\s*\d+\s*页$', r'^页码\s*\d+$',
        # 功能按钮
        r'^搜索$', r'^查找$', r'^筛选$', r'^过滤$', r'^排序$', r'^切换$',
        r'^展开$', r'^收起$', r'^更多$', r'^详情$', r'^查看$',
        # 表单按钮
        r'^提交$', r'^确定$', r'^取消$', r'^重置$', r'^保存$', r'^删除$',
        r'^编辑$', r'^修改$', r'^添加$', r'^新增$',
        # 英文按钮
        r'^post$', r'^new post$', r'^create$', r'^login$', r'^register$',
        r'^search$', r'^more$', r'^next$', r'^prev$', r'^home$',
    ]
    
    # 默认包含关键词（用于向后兼容）
    default_button_keywords = [
        '回复', '编辑', '删除', '举报', '分享', '点赞', '收藏',
        '提交', '确定', '取消', '关闭', '展开', '收起',
        'reply', 'edit', 'delete', 'report', 'share', 'like', 'save',
        'submit', 'ok', 'cancel', 'close', 'expand', 'collapse',
    ]
    
    text_clean = text.strip()
    
    # 首先检查精确匹配模式
    for pattern in exact_button_patterns:
        if re.search(pattern, text_clean, re.IGNORECASE):
            return True
    
    # 然后检查包含关键词
    text_lower = text_clean.lower()
    
    for keyword in default_button_keywords:
        if keyword.lower() in text_lower:
            return True
    
    # 检查是否为纯数字、符号或单字符
    if re.match(r'^[\d\s\-_\+\.]+$|^.$', text_clean):
        return True
    
    return False

def _is_excluded_content(text: str) -> bool:
    """检查内容是否应被排除"""
    if not text:
        return True
    
    excluded_keywords = [
        '发帖', '登录', '注册', '排序', '筛选', '页', '菜单', 
        '导航', '搜索', '设置', '帮助', '关于'
    ]
    
    text_lower = text.lower().strip()
    return any(keyword.lower() in text_lower for keyword in excluded_keywords)

def test_filtering_improvements():
    """测试筛选机制改进效果"""
    print("=== 测试改进后的筛选机制 ===\n")
    
    # 测试案例
    test_cases = [
        # 应该被识别为按钮的文本
        ("我要发帖", True, "发帖按钮"),
        ("发帖", True, "发帖按钮"),
        ("登录", True, "登录按钮"),
        ("注册", True, "注册按钮"),
        ("上一页", True, "分页按钮"),
        ("下一页", True, "分页按钮"),
        ("首页", True, "导航按钮"),
        ("搜索", True, "搜索按钮"),
        ("排序方式：", True, "排序控件"),
        ("第 1 页", True, "分页信息"),
        ("共 1 页", True, "分页信息"),
        ("更多", True, "功能按钮"),
        ("详情", True, "功能按钮"),
        ("1", True, "单字符"),
        ("123", True, "纯数字"),
        
        # 应该通过的真实帖子标题
        ("关于课程选择的建议", False, "正常帖子标题"),
        ("新生入学指南", False, "正常帖子标题"),
        ("学校生活分享", False, "正常帖子标题"),
        ("讨论：最好的学习方法", False, "正常帖子标题"),
        ("寻找室友", False, "正常帖子标题"),
        ("校园活动推荐", False, "正常帖子标题"),
        ("期末复习资料整理", False, "正常帖子标题"),
        ("How to improve English", False, "英文帖子标题"),
        ("Study group formation", False, "英文帖子标题"),
        
        # 边界情况
        ("", True, "空字符串"),
        ("   ", True, "空白字符"),
        ("a", True, "单字母"),
        ("论坛文章", False, "论坛标题"),
        ("关于发帖规则的讨论", False, "包含'发帖'但是正常讨论"),
        ("如何在论坛发帖？", False, "包含'发帖'但是正常提问"),
    ]
    
    print("测试按钮文本识别:")
    print("=" * 50)
    
    passed = 0
    total = len(test_cases)
    
    for text, expected_is_button, description in test_cases:
        is_button = _is_button_text(text)
        is_excluded = _is_excluded_content(text)
        
        # 判断是否应该被过滤掉
        should_be_filtered = is_button or is_excluded
        
        # 检查结果
        result_correct = (should_be_filtered == expected_is_button)
        
        if result_correct:
            passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        print(f"{status} '{text}' -> 按钮:{is_button}, 排除:{is_excluded}, "
              f"预期:{'过滤' if expected_is_button else '通过'}, "
              f"实际:{'过滤' if should_be_filtered else '通过'} ({description})")
    
    print(f"\n测试结果: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    print(f"\n=== 特定案例分析 ===")
    print("分析论坛中发现的问题案例:")
    
    forum_cases = [
        "我要发帖",
        "论坛文章", 
        "排序方式：",
        "上一页",
        "下一页",
        "登录",
        "注册"
    ]
    
    for text in forum_cases:
        is_button = _is_button_text(text)
        is_excluded = _is_excluded_content(text)
        should_filter = is_button or is_excluded
        
        print(f"'{text}' -> {'❌ 过滤' if should_filter else '✅ 通过'} "
              f"(按钮:{is_button}, 排除:{is_excluded})")

if __name__ == "__main__":
    test_filtering_improvements()
