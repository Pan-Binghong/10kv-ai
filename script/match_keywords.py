import re

def filter_religious_sentences(text: str) -> str:
    """
    过滤文本中包含宗教相关关键词的句子,返回不包含关键词的句子
    
    Args:
        text: 输入的文本字符串
        
    Returns:
        str: 不包含宗教关键词的句子,以换行符分隔
    """
    # 提取所有中文句子（包括以 "。？！" 结尾的）
    sentences = re.findall(r'[^。？！\n.,]+[。？！.,]', text)
    
    # 宗教相关关键词匹配模式
    pattern = r'(神|佛|教|灵|上天|圣)'
    
    # 过滤不包含关键词的句子
    unmatched = []
    for s in sentences:
        s = s.strip()
        if not re.search(pattern, s):
            unmatched.append(s)
            
    # 将结果组合成字符串返回
    return '\n'.join(unmatched)

if __name__ == '__main__':
    # 测试文本
    test_text = """
    这是一个普通的句子。
    佛祖保佑平安。刚刚.
    今天天气真不错。
    神灵显灵保佑我们。
    我们要好好学习。
    圣诞节快到了。
    这个教堂很漂亮。
    """
    
    # 调用函数过滤宗教相关句子
    result = filter_religious_sentences(test_text)
    
    # 打印结果
    print("过滤后的句子:")
    print(result)