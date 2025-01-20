import uvicorn
import webbrowser
import os
from pathlib import Path

def main():
    # 确保工作目录正确
    os.chdir(Path(__file__).parent.parent)
    
    # 打开默认浏览器
    webbrowser.open('http://localhost:8000')
    
    # 启动服务器，修改导入路径
    uvicorn.run("webpage.backend.api:app", 
                host="0.0.0.0", 
                port=8000, 
                reload=True,
                reload_dirs=[str(Path(__file__).parent.parent)])  # 添加监视目录

if __name__ == "__main__":
    main() 