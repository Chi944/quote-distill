// The encoder tagger in the browser: tokenize as training did, run the ONNX model, read labels off the logits.
import { AutoModelForTokenClassification, AutoTokenizer, type ProgressCallback, Tensor } from "@huggingface/transformers";
import type { Label } from "../core/expand";
import { byteLevelOffsets } from "../core/offsets";
import { type Offset, read } from "../core/tokens";

export const MAX_LENGTH = 1024; // tagger.MAX_LENGTH
export type Dtype = "fp32" | "q8";

export interface Tagger {
  extract(text: string): Promise<{ label: Label; tokens: number; truncated: boolean }>;
}

export async function loadTagger(path: string, dtype: Dtype, progress?: ProgressCallback): Promise<Tagger> {
  const tokenizer = await AutoTokenizer.from_pretrained(path, { progress_callback: progress });
  const model = await AutoModelForTokenClassification.from_pretrained(path, { dtype, progress_callback: progress });
  const special = new Set<string>(tokenizer.all_special_tokens);
  return {
    async extract(text) {
      // The underlying tokenizer gives token strings, from which offsets are derived (it reports none itself).
      const enc = tokenizer._tokenizer.encode(text);
      let ids: number[] = enc.ids;
      let offsets: Offset[] = byteLevelOffsets(text, enc.tokens, special);
      const truncated = ids.length > MAX_LENGTH;
      if (truncated) {
        // As Python truncates [CLS] ... [SEP]: keep the first MAX_LENGTH - 1 tokens, then the closing [SEP].
        ids = [...ids.slice(0, MAX_LENGTH - 1), ids.at(-1)!];
        offsets = [...offsets.slice(0, MAX_LENGTH - 1), offsets.at(-1)!];
      }
      const shape = [1, ids.length];
      const out = await model({
        input_ids: new Tensor("int64", BigInt64Array.from(ids, BigInt), shape),
        attention_mask: new Tensor("int64", new BigInt64Array(ids.length).fill(1n), shape),
      });
      const [, n, labels] = out.logits.dims as number[];
      const data = out.logits.data as Float32Array;
      const rows = Array.from({ length: n! }, (_, i) => data.subarray(i * labels!, (i + 1) * labels!));
      return { label: read(text, offsets, rows), tokens: enc.ids.length, truncated };
    },
  };
}
