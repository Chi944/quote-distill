/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Where the model folders live when not next to the page, e.g. https://huggingface.co/<repo>/resolve/main/ */
  readonly VITE_MODEL_BASE?: string;
}
