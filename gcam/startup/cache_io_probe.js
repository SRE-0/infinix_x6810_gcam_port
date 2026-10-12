// RETIRED EXPERIMENT: caused startup SIGSEGV on Android 16; no valid evidence.
// Do not use for benchmarking or the retained module. See GCAM_REMAINING_REVIEW_20261011.md.
// Read-only native I/O observation. Version-specific JNI offset guarded by runner.
const cachePrefix = '/storage/emulated/0/Android/data/com.android.MGC_9_7_047/cache';
for (const name of ['open', 'open64', 'openat', 'openat64', 'fopen', 'fopen64']) {
  const address = Module.findGlobalExportByName(name);
  if (!address) continue;
  Interceptor.attach(address, {
    onEnter(args) {
      const index = name.startsWith('openat') ? 1 : 0;
      try {
        this.path = args[index].readCString();
        if (!this.path.startsWith(cachePrefix)) { this.path = null; return; }
        this.mode = name.startsWith('fopen') ? args[index + 1].readCString() : args[index + 1].toInt32();
        this.stack = Thread.backtrace(this.context, Backtracer.ACCURATE).slice(0, 16).map(p => {
          const m = Process.findModuleByAddress(p);
          return m ? m.name + '+' + p.sub(m.base) : p.toString();
        });
      } catch (_) { this.path = null; }
    },
    onLeave(result) {
      if (this.path) send({event:'cache_io', api:name, path:this.path, mode:this.mode,
        result:result.toString(), errno:this.errno, tid:Process.getCurrentThreadId(), stack:this.stack});
    }
  });
}
Process.attachModuleObserver({onAdded(m) {
  if (m.name !== 'libgcastartup.so') return;
  Interceptor.attach(m.base.add(0x23a9704), {
    onEnter(args) {
      this.begin = Date.now();
      const env = args[0], table = env.readPointer();
      const get = new NativeFunction(table.add(169 * Process.pointerSize).readPointer(), 'pointer', ['pointer','pointer','pointer']);
      const release = new NativeFunction(table.add(170 * Process.pointerSize).readPointer(), 'void', ['pointer','pointer','pointer']);
      const model = get(env,args[4],ptr(0));
      const modelText = model.readCString();
      release(env,args[4],model);
      const cache = get(env,args[5],ptr(0));
      const cacheText = cache.readCString();
      release(env,args[5],cache);
      send({event:'segmenter_enter', model:modelText, cache:cacheText, tid:Process.getCurrentThreadId()});
    },
    onLeave(result) { send({event:'segmenter_exit', ok:result.toInt32(), elapsed_ms:Date.now()-this.begin}); }
  });
  send({event:'hook_ready', module:m.name});
}});
