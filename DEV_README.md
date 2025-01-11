## 安裝 開發 打包 

    conda create -n directory_scanner python=3.11

    conda activate directory_scanner

    pip install pyinstaller PyQt5 Pillow

    pip install pyyaml 多語言檔案
     
    pip install humanize 格式化文件大小

    pip install reportlab 生成pdf


### 設定pip源

    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple    

### M Chip版本
    pyinstaller --windowed --onefile --icon=app_logo.ico --add-data "DroidSansFallback.ttf:." --add-data "config.yaml:." --add-data "logo.png:." --clean --noconfirm qt_main.py -n "Directory Scanner v1.1.1 M Chip"
    

### Intel Chip版本
 

### Create DMG

    create-dmg \
    --volname "Directory Scanner v1.1.1 M Chip" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --app-drop-link 600 185 \
    "Directory-Scanner-v1-1-1-M-Chip.dmg" \
    "dist/Directory Scanner v1.1.1 M Chip.app"

### Create DMG (Add Manual PDF & Marker.xml)
    mkdir -p tmp_dmg
    cp -r "dist/Directory Scanner v1.1.1 M Chip.app" tmp_dmg/    
    cp DroidSansFallback.ttf tmp_dmg/
    cp logo.png tmp_dmg/
    # 2. 使用 create-dmg 创建带有 Applications 快捷方式的 DMG
    create-dmg \
        --volname "Directory Scanner v1.1.1 M Chip" \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --icon "Directory Scanner v1.1.1 M Chip.app" 200 185 \
        --app-drop-link 600 185 \
        --add-file "DroidSansFallback.ttf" DroidSansFallback.ttf 400 185 \
        --add-file "logo.png" logo.png 400 185 \
        "Directory-Scanner-v1.1.1-M-Chip.dmg" \
        "tmp_dmg/"

    # 3. 清理临时文件
    rm -rf tmp_dmg
           
## 程式結構
        
    qt_main.py
    dir_scanner.py

## GitHub

    cd (DIR)
    git init
    edit .gitignore

    git status
    git add .
    git commit -m "First Commit"

    git branch -M main    
    git remote add origin https://github.com/gumpcpy/directory_scanner.git                          
    git push -u origin main


## 移植 重建環境

    conda env export > environment.yml

    或更好的

    conda env export --from-history > environment.yml

    --from-history 選項只會記錄您明確安裝的包，而不是所有依賴，這樣可以創建一個更清晰的配置文件。

    在別的電腦導入

    conda env create -f environment.yml

    這樣可以確保在不同平台（如 M1 Mac 和 Intel Mac）上都能正確重現環境



