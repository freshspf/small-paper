baseline_result 公平抽样说明

输入目录：/Users/ning/Developer/project26/exps/chapter3v0323/chapter4/exp_4_5/baseline_result
输出表：/Users/ning/Developer/project26/exps/chapter3v0323/chapter4/exp_4_5/tables/baseline_axiom_annotation_sampled_300_fair.csv

规则：
1. 以论文为单位均衡抽样，每篇目标 10 条，总计 300 条。
2. 每篇先尽量覆盖四类公理：subClassOf、subPropertyOf、domain、range。
3. 若某篇某类公理不存在，则从该篇其他类型中补足到约 10 条。
4. 二次补样时限制单一类型过度主导；不足时再放宽补满。
5. 随机种子固定为 20260417，可复现。
