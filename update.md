# Update Log for Students 給學生們的更新紀錄

Due to the potential issues that may arise with this assignment, the teaching assistants will update this Repository based on student feedback to facilitate downloading the latest files and tracking the most recent updates. Please refer to this update log while working on the assignment.

由於本次作業可能會遇到不少問題，助教將根據學生的回饋更新本 Repository，以利學生下載最新的檔案並追蹤最新的更新情況。請同學參考本更新紀錄進行作業。

## Download Instructions 下載方法

Assuming your mp2 is located in the `os/mp2/mp2-<USERNAME>` folder, please download the [update.sh](./update.sh) script to `os/mp2/mp2-<USERNAME>` and run the following command. This assumes that you have not made additional modifications to restricted files, and it will automatically update all restricted files.

假設同學的 mp2 在 `os/mp2/mp2-<USERNAME>` 資料夾下，請下載 [update.sh](./update.sh) 腳本至 `os/mp2/mp2-<USERNAME>` 並運行以下命令，其假設同學沒有在受限制的檔案進行額外的修改，自動更新所有受限制的檔案。

```bash
./update.sh
```

!!! Please note that students must not submit the limited updated files. !!!

!!! 請同學們注意，務必不要將更新的受限制檔案提交。!!!

## Changelog 更新日誌

| Date  | Commit (View Changed Files)                                                                                                                | Reference Discussion Thread Link                                      |
|-------|:-------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------|
| 3/22  | [[platform] Add arm64 support](https://github.com/Shiritai/xv6-ntu-mp2/commit/0264b3f168121e3c555799ebde20ba83d32864df)                  | https://cool.ntu.edu.tw/courses/46296/discussion_topics/381980 |
| 3/22  | [[scripts] Fix mp2.sh issue](https://github.com/Shiritai/xv6-ntu-mp2/commit/13fe8c5beb6f9688df2c5f60a7200ea954ba59f3)                    | https://cool.ntu.edu.tw/courses/46296/discussion_topics/381980 |
| 3/22  | [[doc] Update alloc flowchart](https://github.com/Shiritai/xv6-ntu-mp2/commit/3b6f1dd3241a20168add9be0bef16a6dfa10d531)                  | https://cool.ntu.edu.tw/courses/46296/discussion_topics/382170 |
| 3/24  | [Add better mp0,1 compatible commands](https://github.com/Shiritai/xv6-ntu-mp2/commit/238354551f3a1762ea9e23925ce90aa7ae8c228c)          | https://cool.ntu.edu.tw/courses/46296/discussion_topics/382503 |
| 3/24  | [[user] Fix gah/oak timeout issue](https://github.com/Shiritai/xv6-ntu-mp2/commit/54a78c1d5b8a5c281d24075397bc1b46a06d9380)              | https://cool.ntu.edu.tw/courses/46296/discussion_topics/382615 |
| 3/24  | [[doc] Update of dev using vscode in container](https://github.com/Shiritai/xv6-ntu-mp2/commit/382f9873b30319903459a4e85384f1f1cf5946d6) | https://cool.ntu.edu.tw/courses/46296/discussion_topics/382476 |
| 3/24  | [[doc] Fix typo of obj_size](https://github.com/Shiritai/xv6-ntu-mp2/commit/e2dba993538ac25c765a8b117d0c06ae3d07094e) | https://cool.ntu.edu.tw/courses/46296/discussion_topics/382881 |
| 3/24  | [[test] Upgrade testing system](https://github.com/Shiritai/xv6-ntu-mp2/commit/7adaa7887306885c2f865925c75708fc96854af4) | https://cool.ntu.edu.tw/courses/46296/discussion_topics/382429 <br> https://cool.ntu.edu.tw/courses/46296/discussion_topics/382615 <br> https://cool.ntu.edu.tw/courses/46296/discussion_topics/382443 |
| 3/26  | [[doc] Batched update on doc and test](https://github.com/Shiritai/xv6-ntu-mp2/commit/6e32c2d585cd9aeb18fcae4b0cf0b8d2d3ece971) | https://cool.ntu.edu.tw/courses/46296/discussion_topics/383137 (more flexible slab name) <br> https://cool.ntu.edu.tw/courses/46296/discussion_topics/383420 (typo bus) <br> Questions from email |
| 3/27  | [[scripts] Update git hook](https://github.com/Shiritai/xv6-ntu-mp2/commit/0cc477b1dd5fd2aab95adeef9b9d08c29f275010) <br> [[doc] Revision to the spec](https://github.com/Shiritai/xv6-ntu-mp2/commit/2686b8a8bc3601905c3d7bebd0fb7ec1a2f3699d) <br> [[test] Update error message and enhance robustness](https://github.com/Shiritai/xv6-ntu-mp2/commit/5526338b26f47f1450fabc2ebe618458d5043a7b) <br> [[test] Update timeout limit](https://github.com/Shiritai/xv6-ntu-mp2/commit/619fb28e1e34c0b6d53a73afb4f91f8433ccfccb) | Mainly based on TA hour |
| 3/27  | [[test] Important update to the feature tests](https://github.com/Shiritai/xv6-ntu-mp2/commit/7de0551c42ccd8242dcc08b1d0d938b20d99fb4e) | https://cool.ntu.edu.tw/courses/46296/discussion_topics/383526 <br> https://cool.ntu.edu.tw/courses/46296/discussion_topics/383849 <br> https://cool.ntu.edu.tw/courses/46296/discussion_topics/384179, etc. |
