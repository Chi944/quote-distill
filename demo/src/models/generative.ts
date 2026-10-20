// The generative student in the browser: the training prompt, greedy decoding, then the same JSON parse as Python.
import { AutoModelForCausalLM, AutoTokenizer } from "@huggingface/transformers";
import { type Label, parseOutput } from "../core/expand";

export const PROMPT = "Extract the supplier quotation below as compact JSON.\n### Quotation\n{text}\n### JSON\n"; // generative.PROMPT
export const MAX_NEW_TOKENS = 768;
export type Dtype = "fp32" | "q8" | "q4";

export interface Generative {
  /** The raw output and its parse; `label` is null when the output isn't one compact JSON object. */
  extract(text: string, maxNewTokens?: number): Promise<{ output: string; label: Label | null }>;
}

export const prompt = (text: string) => PROMPT.replace("{text}", () => text);

export async function loadGenerative(path: string, dtype: Dtype): Promise<Generative> {
  const tokenizer = await AutoTokenizer.from_pretrained(path);
  const model = await AutoModelForCausalLM.from_pretrained(path, { dtype });
  return {
    async extract(text, maxNewTokens = MAX_NEW_TOKENS) {
      const enc = tokenizer(prompt(text), { add_special_tokens: false, return_token_type_ids: false });
      const ids = (await model.generate({ ...enc, max_new_tokens: maxNewTokens, do_sample: false })) as { tolist(): bigint[][] };
      const all = ids.tolist()[0]!;
      const output = tokenizer.decode(all.slice(enc.input_ids.dims.at(-1)!), { skip_special_tokens: true });
      return { output, label: parseOutput(output) };
    },
  };
}
