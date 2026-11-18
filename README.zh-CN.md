# SMEDecode

[English](README.md)

SMEDecode面向Arm SME上的注意力解码。`bench_aarch64` 是论文中SMEDecode与独立复现的SMEAtten进行对比时所用的AArch64 Linux静态链接程序。此二进制文件取自已归档的原对比构建。[论文入口（Overleaf，需项目权限）](https://www.overleaf.com/project/6abc585ad54da187b60b59df)

## 运行功能测试

在Linux终端进入仓库根目录，执行：

```sh
python3 smoke_test.py
```

脚本需要4个可用CPU。在Arm64上直接运行，要求处理器支持SME和SVE2，流式向量长度为512位。其他架构通过带SME仿真的 `qemu-aarch64` 运行。程序自动生成输入，用FP64参考值核对两种方法在4个小规模配置下的输出。测试文件保存在临时目录，脚本退出时清理。完整的性能测量依赖原实验服务器及其资源分配和NUMA绑定输入。

[第三方许可声明](THIRD_PARTY_NOTICES.txt)
