"use client";

import { useMemo, useState, useTransition } from "react";

import {
  createModelConfig,
  deleteModelConfig,
  type ModelConfigPayload,
  updateModelConfig,
} from "@/lib/api";
import { type ModelConfigItem } from "@/lib/mock-data";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";


type ModelTableProps = {
  models: ModelConfigItem[];
};

type FormState = {
  modelName: string;
  modelCode: string;
  apiUrl: string;
  apiKey: string;
  temperature: string;
  maxTokens: string;
  status: number;
};


const EMPTY_FORM: FormState = {
  modelName: "",
  modelCode: "",
  apiUrl: "",
  apiKey: "",
  temperature: "0.20",
  maxTokens: "4096",
  status: 1,
};


function toFormState(model: ModelConfigItem): FormState {
  return {
    modelName: model.modelName,
    modelCode: model.modelCode,
    apiUrl: model.apiUrl,
    apiKey: model.apiKey,
    temperature: model.temperature.toFixed(2),
    maxTokens: String(model.maxTokens),
    status: model.status,
  };
}


function toPayload(formState: FormState): ModelConfigPayload {
  return {
    modelName: formState.modelName.trim(),
    modelCode: formState.modelCode.trim(),
    apiUrl: formState.apiUrl.trim(),
    apiKey: formState.apiKey.trim(),
    temperature: Number(formState.temperature),
    maxTokens: Number(formState.maxTokens),
    status: Number(formState.status),
  };
}


export function ModelTable({ models }: ModelTableProps) {
  const [items, setItems] = useState(models);
  const [isPending, startTransition] = useTransition();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingModelId, setEditingModelId] = useState<number | null>(null);
  const [formState, setFormState] = useState<FormState>(EMPTY_FORM);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const activeCount = useMemo(() => items.filter((item) => item.status === 1).length, [items]);
  const dialogTitle = editingModelId === null ? "新增模型配置" : "编辑模型配置";

  function openCreateDialog() {
    setEditingModelId(null);
    setFormState(EMPTY_FORM);
    setErrorMessage(null);
    setIsDialogOpen(true);
  }

  function openEditDialog(model: ModelConfigItem) {
    setEditingModelId(model.id);
    setFormState(toFormState(model));
    setErrorMessage(null);
    setIsDialogOpen(true);
  }

  function closeDialog() {
    setIsDialogOpen(false);
    setEditingModelId(null);
    setFormState(EMPTY_FORM);
    setErrorMessage(null);
  }

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setFormState((current) => ({
      ...current,
      [key]: value,
    }));
  }

  function maskApiKey(apiKey: string) {
    if (apiKey.length <= 8) {
      return apiKey ? "****" : "--";
    }
    return `${apiKey.slice(0, 4)}***${apiKey.slice(-4)}`;
  }

  function validatePayload(payload: ModelConfigPayload) {
    if (!payload.modelName || !payload.modelCode || !payload.apiUrl || !payload.apiKey) {
      return "请填写模型名称、调用标识、接口地址和接口密钥。";
    }
    if (Number.isNaN(payload.temperature) || payload.temperature < 0 || payload.temperature > 9.99) {
      return "温度参数需要在 0 到 9.99 之间。";
    }
    if (!Number.isInteger(payload.maxTokens) || payload.maxTokens <= 0) {
      return "最大输出长度必须是正整数。";
    }
    return null;
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);

    const payload = toPayload(formState);
    const validationError = validatePayload(payload);
    if (validationError) {
      setErrorMessage(validationError);
      return;
    }

    startTransition(async () => {
      try {
        if (editingModelId === null) {
          const created = await createModelConfig(payload);
          setItems((current) => [created, ...current]);
        } else {
          const updated = await updateModelConfig(editingModelId, payload);
          setItems((current) => current.map((item) => (item.id === updated.id ? updated : item)));
        }
        closeDialog();
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "提交失败，请稍后重试。");
      }
    });
  }

  function handleDelete(model: ModelConfigItem) {
    const confirmed = window.confirm(`确认删除模型配置“${model.modelName}”吗？`);
    if (!confirmed) {
      return;
    }

    setErrorMessage(null);
    startTransition(async () => {
      try {
        await deleteModelConfig(model.id);
        setItems((current) => current.filter((item) => item.id !== model.id));
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "删除失败，请稍后重试。");
      }
    });
  }

  function toggleStatus(model: ModelConfigItem) {
    const nextStatus = model.status === 1 ? 0 : 1;
    startTransition(async () => {
      try {
        const updated = await updateModelConfig(model.id, {
          modelName: model.modelName,
          modelCode: model.modelCode,
          apiUrl: model.apiUrl,
          apiKey: model.apiKey,
          temperature: model.temperature,
          maxTokens: model.maxTokens,
          status: nextStatus,
        });
        setItems((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "状态切换失败，请稍后重试。");
      }
    });
  }

  return (
    <>
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="px-5 py-4">
          <p className="text-sm text-slate-500">模型配置总数</p>
          <p className="mt-2 text-2xl font-semibold text-ink">{items.length}</p>
        </Card>
        <Card className="px-5 py-4">
          <p className="text-sm text-slate-500">启用模型</p>
          <p className="mt-2 text-2xl font-semibold text-ink">{activeCount}</p>
        </Card>
        <Card className="px-5 py-4">
          <p className="text-sm text-slate-500">配置字段</p>
          <p className="mt-2 text-2xl font-semibold text-ink">8</p>
        </Card>
      </div>

      <Card className="overflow-hidden">
        <div className="flex items-center justify-between border-b border-line px-6 py-5">
          <div>
            <h3 className="text-lg font-semibold text-ink">模型配置列表</h3>
            <p className="text-sm text-slate-600">维护模型调用标识、接口地址、密钥和推理参数。</p>
          </div>
          <Button variant="secondary" onClick={openCreateDialog}>
            新增配置
          </Button>
        </div>

        {errorMessage ? (
          <div className="border-b border-line bg-amber-50 px-6 py-3 text-sm text-amber-700">{errorMessage}</div>
        ) : null}

        {items.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <p className="text-base font-medium text-ink">当前尚未配置模型</p>
            <p className="mt-2 text-sm text-slate-500">可以点击右上角“新增配置”开始录入模型调用信息。</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="paper-table min-w-[980px]">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>模型显示名称</th>
                  <th>模型调用标识</th>
                  <th>接口地址</th>
                  <th>API Key</th>
                  <th>温度</th>
                  <th>最大输出</th>
                  <th>状态</th>
                  <th>更新时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {items.map((model) => (
                  <tr key={model.id}>
                    <td>{model.id}</td>
                    <td>{model.modelName}</td>
                    <td>{model.modelCode}</td>
                    <td className="max-w-[220px] truncate">{model.apiUrl}</td>
                    <td>{maskApiKey(model.apiKey)}</td>
                    <td>{model.temperature.toFixed(2)}</td>
                    <td>{model.maxTokens}</td>
                    <td>
                      <Badge variant={model.status === 1 ? "success" : "muted"}>
                        {model.status === 1 ? "启用" : "停用"}
                      </Badge>
                    </td>
                    <td>{model.updatedTime}</td>
                    <td>
                      <div className="flex gap-2">
                        <Button variant="outline" className="px-3 py-2 text-xs" onClick={() => openEditDialog(model)}>
                          编辑
                        </Button>
                        <Button variant="outline" className="px-3 py-2 text-xs" onClick={() => toggleStatus(model)}>
                          {model.status === 1 ? "停用" : "启用"}
                        </Button>
                        <Button variant="outline" className="px-3 py-2 text-xs" onClick={() => handleDelete(model)}>
                          删除
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {isDialogOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1F2933]/35 px-4 py-10">
          <div className="paper-dialog max-w-3xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-xl font-semibold text-ink">{dialogTitle}</h3>
                <p className="mt-2 text-sm text-slate-600">配置模型调用所需的接口参数，便于后续实验任务复用。</p>
              </div>
              <Button variant="outline" onClick={closeDialog}>
                关闭
              </Button>
            </div>

            <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
              <div className="grid gap-5 md:grid-cols-2">
                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">模型显示名称</span>
                  <input
                    className="paper-input"
                    value={formState.modelName}
                    onChange={(event) => updateField("modelName", event.target.value)}
                    placeholder="例如：Claude Sonnet 4.6"
                    required
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">模型调用标识</span>
                  <input
                    className="paper-input"
                    value={formState.modelCode}
                    onChange={(event) => updateField("modelCode", event.target.value)}
                    placeholder="例如：claude-sonnet-4-6"
                    required
                  />
                </label>

                <label className="space-y-2 md:col-span-2">
                  <span className="text-sm font-medium text-ink">接口地址</span>
                  <input
                    className="paper-input"
                    value={formState.apiUrl}
                    onChange={(event) => updateField("apiUrl", event.target.value)}
                    placeholder="https://api.example.com/v1"
                    required
                  />
                </label>

                <label className="space-y-2 md:col-span-2">
                  <span className="text-sm font-medium text-ink">接口密钥</span>
                  <input
                    className="paper-input"
                    value={formState.apiKey}
                    onChange={(event) => updateField("apiKey", event.target.value)}
                    placeholder="sk-..."
                    required
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">温度参数</span>
                  <input
                    className="paper-input"
                    type="number"
                    min="0"
                    max="9.99"
                    step="0.01"
                    value={formState.temperature}
                    onChange={(event) => updateField("temperature", event.target.value)}
                    required
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">最大输出长度</span>
                  <input
                    className="paper-input"
                    type="number"
                    min="1"
                    step="1"
                    value={formState.maxTokens}
                    onChange={(event) => updateField("maxTokens", event.target.value)}
                    required
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium text-ink">启用状态</span>
                  <select
                    className="paper-input"
                    value={formState.status}
                    onChange={(event) => updateField("status", Number(event.target.value))}
                  >
                    <option value={1}>启用</option>
                    <option value={0}>停用</option>
                  </select>
                </label>
              </div>

              {errorMessage ? <p className="text-sm text-amber-700">{errorMessage}</p> : null}

              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" onClick={closeDialog}>
                  取消
                </Button>
                <Button type="submit" variant="secondary" disabled={isPending}>
                  {isPending ? "提交中..." : editingModelId === null ? "创建配置" : "保存修改"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </>
  );
}
