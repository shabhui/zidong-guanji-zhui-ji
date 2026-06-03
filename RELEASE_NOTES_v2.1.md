# AutoShutdownQt 2.1 Release Notes

AutoShutdownQt 2.1 是 Windows 便携版自动电源动作工具，基于 Python + PySide6/QML。

## 发布产物

- 便携版目录：`dist/AutoShutdownQt-2.1/`
- 便携版 zip：`dist/AutoShutdownQt-2.1.zip`
- 校验文件：`dist/SHA256SUMS.txt`
- 发布检查清单：`dist/release-checklist-v2.1.md`
- zip 内包含：`AutoShutdownQt.exe`、QML 资源、`release-manifest.json`

## 安全说明

- 默认开启 **Dry-run** 安全模式。
- Dry-run 下不会真实关机、重启、注销、锁定、睡眠或休眠。
- Dry-run 下不会运行执行前脚本，只记录将要执行的脚本路径。
- 关闭 Dry-run 后进入真实执行模式，请先确认动作、触发器、脚本路径、托盘状态和未保存工作。

## 功能摘要

- 多任务队列。
- 固定时间任务支持仅一次、每天、工作日、周末重复规则。
- 倒计时任务进入任务队列。
- 进程退出触发和网络闲置触发会显示为队列任务。
- 托盘后台运行：关闭窗口会隐藏到托盘，托盘 Quit 才显式退出。
- 电源动作：关机、睡眠、休眠、重启、注销、锁定。
- 配置持久化、日志导出和诊断信息。

## 已知说明

- 当前 exe **未做代码签名**，Windows 首次运行可能提示安全警告。
- 当前发布包是便携版，不是安装器。
- PyInstaller/PySide6 打包时可能输出 QML plugin logging warning；只要最终生成 zip 并通过 manifest/QML 校验，该 warning 不阻止本地发布包使用。

## 本地验证清单

发布前建议确认：

```bash
python -m unittest discover AutoShutdownQt/tests -v
python AutoShutdownQt/package_release.py
```

并启动：

```text
dist/AutoShutdownQt-2.1/AutoShutdownQt.exe
```

确认应用可启动，默认仍处于 Dry-run 模式。验证时不要执行真实系统电源动作。
