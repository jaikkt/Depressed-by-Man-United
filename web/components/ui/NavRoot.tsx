"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { isTyping } from "@/lib/input";
import { useSettings } from "@/lib/settings";
import { directionFromKey, moveFocus, ownedByComponent } from "@/lib/spatialNav";

/** Global console behaviour: arrows move focus spatially, Esc/B goes back to
 *  the main menu. Mounted once in the root layout; screens can pre-empt either
 *  behaviour by calling preventDefault in their own key handler. */
export function NavRoot() {
  const router = useRouter();
  const pathname = usePathname();
  const { sfx } = useSettings();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.defaultPrevented || isTyping(e) || e.metaKey || e.ctrlKey || e.altKey) return;
      const dir = directionFromKey(e.key);
      if (dir) {
        if (ownedByComponent(dir)) return;
        if (moveFocus(dir)) e.preventDefault();
        return;
      }
      if (e.key === "Escape" && pathname !== "/") {
        e.preventDefault();
        sfx("back");
        router.push("/");
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [router, pathname, sfx]);

  return null;
}
