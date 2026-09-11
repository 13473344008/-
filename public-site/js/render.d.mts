export interface PreviewOptions { language?: string; previewKind?: string; privateAssets?: Record<string,string> }
export function renderPassport(container: HTMLElement,payload: unknown,options?: PreviewOptions): {product:{name:string};batch:{code:string}};
export function renderError(container:HTMLElement,code:string,retry?:()=>void):void;
