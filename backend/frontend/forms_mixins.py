class TailwindFormMixin:
    def apply_tailwind_classes(self):
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (
                existing
                + " w-full rounded-xl border border-am-border bg-am-alt px-4 py-3 text-[#e0e1ec] placeholder-am-dim focus:outline-none focus:ring-2 focus:ring-am-cyan"
            ).strip()