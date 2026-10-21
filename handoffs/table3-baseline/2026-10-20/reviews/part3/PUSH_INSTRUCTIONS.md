# 用户自行提交 GitHub

所有评分与验证成果都在 `handoffs/table3-baseline/2026-10-20/reviews/part3/`。助手没有 stage、commit 或 push。

`COMMIT_FILES.txt` 是按本次成果白名单生成的仓库相对路径清单，包含报告、结果、代码和核验证据；不会添加解压后的整包、`.DS_Store`、`.Rhistory` 或其他个人文件。

Kyrie 已明确签收 PASS，记录见 [HUMAN_SIGNOFF.md](HUMAN_SIGNOFF.md)。现在可以按下面步骤提交本地 Part3 成果。

从仓库根目录执行。下面分支名供本次提交使用；若你已创建该分支，第二步改为 `git switch part3-scoring-validation`。

```sh
cd "/Users/kyriema/Desktop/CMU/Intro Deep Learning/Project/intro_dl_Team_Project"
git switch -c part3-scoring-validation
python3 -B -X utf8 -S handoffs/table3-baseline/2026-10-20/reviews/part3/evidence/prepare_delivery.py
git add --pathspec-from-file=handoffs/table3-baseline/2026-10-20/reviews/part3/COMMIT_FILES.txt
git diff --cached --stat
git diff --cached --check
git commit -m "Complete Part 3 scoring and validation review"
git push -u origin part3-scoring-validation
```

`git diff --cached --stat` 中应只有 `reviews/part3/` 下的成果。如果你此前自行暂存过其他文件，先在 Git 界面确认是否需要一并提交。然后由你在 GitHub 发起该分支到 main 的 PR，供团队 review。

另一台机器没有解压目录时，先解压仓库已存在的原 ZIP，再运行 prepare_delivery；原 ZIP 无需重新上传。要再次执行完整核验，可使用 [README](README.md) 中的三条命令。
