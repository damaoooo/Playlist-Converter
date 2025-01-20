import json
import os

def get_dev_token():
    """
    从配置文件读取开发者令牌
    返回: str - 开发者令牌
    """
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 'Apple', 'config.json')

        with open(config_path, 'r') as f:
            config = json.load(f)
            dev_token = config.get('jwt')
        
        if not dev_token:
            raise ValueError("配置文件中未找到开发者令牌")
            
        return dev_token
        
    except Exception as e:
        raise Exception(f"获取开发者令牌失败: {str(e)}")

if __name__ == "__main__":
    try:
        token = get_dev_token()
        print(f"开发者令牌: {token}")
    except Exception as e:
        print(f"错误: {e}") 