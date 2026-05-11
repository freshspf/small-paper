from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


def load_text(file_path: str) -> str:
    """
    读取文本文件内容
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.read_text(encoding="utf-8").strip()


def get_domain_hint(domain: str) -> str:
    """
    根据领域名称加载领域提示模块
    支持: medical / geography / transportation
    """
    domain = domain.lower().strip()
    domain_file = f"prompts/modules/domain_{domain}.txt"
    path = BASE_DIR / domain_file

    if not path.exists():
        raise FileNotFoundError(f"未找到领域提示文件: {domain_file}")

    return load_text(str(path))


def get_module_text(is_on: bool, file_path: str) -> str:
    """
    根据开关状态决定是否加载模块文本
    ON -> 读取文件内容
    OFF -> 返回空字符串
    """
    if not is_on:
        return ""

    path = Path(file_path)
    if not path.is_absolute():
        path = BASE_DIR / path
    if not path.exists():
        raise FileNotFoundError(f"未找到模块文件: {file_path}")

    return load_text(str(path))


def build_prompt(config: dict, domain: str, input_text: str) -> str:
    """
    构建最终 prompt

    参数:
        config: 配置字典，例如:
            {
                "count": True,
                "domain": True,
                "naming": False,
                "entity": False
            }
        domain: 领域名称，例如:
            "medical", "geography", "transportation"
        input_text: 输入文本内容

    返回:
        拼接完成的 prompt 字符串
    """

    template_path = "prompts/template/configurable_template.txt"
    template = load_text(template_path)

    # 1. 领域提示
    domain_hint = get_domain_hint(domain) if config.get("domain", False) else ""

    # 2. 数量限制
    count_constraint = get_module_text(
        config.get("count", False),
        "prompts/modules/count_on.txt"
    )

    # 3. 实体定义
    entity_definition = get_module_text(
        config.get("entity", False),
        "prompts/modules/entity_on.txt"
    )

    # 4. 命名规则
    naming_rules = get_module_text(
        config.get("naming", False),
        "prompts/modules/naming_on.txt"
    )

    # 5. 拼接模板
    prompt = (
        template
        .replace("{DOMAIN_HINT}", domain_hint)
        .replace("{COUNT_CONSTRAINT}", count_constraint)
        .replace("{ENTITY_DEFINITION}", entity_definition)
        .replace("{NAMING_RULES}", naming_rules)
        .replace("{text}", input_text)
    )

    return prompt


if __name__ == "__main__":
    # 示例配置：第3轮
    config_round3 = {
        "count": True,
        "domain": True,
        "naming": True,
        "entity": False
    }

    sample_text = """
    Diabetes is a chronic disease characterized by elevated blood glucose levels.
    Insulin therapy is commonly used to treat patients with diabetes.
    """

    prompt = build_prompt(
        config=config_round3,
        domain="medical",
        input_text=sample_text
    )

    print(prompt)
