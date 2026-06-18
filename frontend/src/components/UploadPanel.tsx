import { useCallback, useRef, useState } from "react";
import { UploadCloud, ImageIcon } from "lucide-react";

export function UploadPanel({
  previewUrl,
  filename,
  disabled,
  onFile,
}: {
  previewUrl: string | null;
  filename: string | null;
  disabled: boolean;
  onFile: (f: File) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  const pick = useCallback(
    (files: FileList | null) => {
      const f = files?.[0];
      if (f && f.type.startsWith("image/")) onFile(f);
    },
    [onFile],
  );

  return (
    <div className="p-4">
      <h2 className="mb-3 font-mono text-xs font-semibold uppercase tracking-widest text-slate-300">
        Input image
      </h2>

      <div
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          if (!disabled) pick(e.dataTransfer.files);
        }}
        className={`group relative flex aspect-square cursor-pointer items-center justify-center overflow-hidden rounded-lg border-2 border-dashed transition-colors ${
          drag ? "border-emerald-500 bg-emerald-500/5" : "border-slate-700 hover:border-slate-600"
        } ${disabled ? "pointer-events-none opacity-60" : ""}`}
      >
        {previewUrl ? (
          <img src={previewUrl} alt="input" className="h-full w-full object-contain" />
        ) : (
          <div className="flex flex-col items-center gap-2 text-slate-500">
            <UploadCloud className="h-8 w-8" strokeWidth={1.3} />
            <p className="px-4 text-center font-mono text-[11px] leading-relaxed">
              drop a product image
              <br />
              or click to browse
            </p>
          </div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => pick(e.target.files)}
        />
      </div>

      {filename && (
        <p className="mt-2 flex items-center gap-1.5 truncate font-mono text-[11px] text-slate-500">
          <ImageIcon className="h-3 w-3 shrink-0" /> {filename}
        </p>
      )}
    </div>
  );
}
