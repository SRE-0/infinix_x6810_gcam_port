// APK-specific transient diagnostic. No HAL hooks, image reads or disk patches.
for (const name of ['open', 'open64', 'openat', 'openat64']) {
  const address = Module.findGlobalExportByName(name);
  if (!address) continue;
  Interceptor.attach(address, {onEnter(a) {
    const index = name.startsWith('openat') ? 1 : 0;
    let path;
    try { path = a[index].readCString(); } catch (_) { return; }
    if (path !== '/storage/emulated/0/Android/data/com.android.MGC_9_7_047/cache') return;
    const flags = a[index + 1].toInt32();
    send({event: 'cache_directory_open', name, flags, stack: Thread.backtrace(this.context, Backtracer.ACCURATE).slice(0,8).map(p => DebugSymbol.fromAddress(p).toString())});
  }});
}
Process.attachModuleObserver({onAdded(m) {
  if (m.name !== 'libgcastartup.so') return;
  Interceptor.attach(m.base.add(0x23a9704), {
    onEnter(a) {
      this.begin = Date.now();
      const env = a[0], table = env.readPointer();
      const get = new NativeFunction(table.add(169 * Process.pointerSize).readPointer(), 'pointer', ['pointer', 'pointer', 'pointer']);
      const release = new NativeFunction(table.add(170 * Process.pointerSize).readPointer(), 'void', ['pointer', 'pointer', 'pointer']);
      const str = get(env, a[5], ptr(0));
      const original = str.readCString();
      release(env, a[5], str);
      send({event: 'segmenter_enter', original_cache: original, time: this.begin});
    },
    onLeave(r) { send({event: 'segmenter_exit', ok: r.toInt32(), elapsed_ms: Date.now() - this.begin}); }
  });
  send({event: 'hook_ready', module: m.name});
}});
