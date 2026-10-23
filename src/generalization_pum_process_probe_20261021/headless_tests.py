"""Four invented forwarding/restoration cases, with no native/scientific work."""
import types
import unittest
from unittest.mock import patch
from . import headless as h


class HeadlessTests(unittest.TestCase):
    def test_only_creation_flags_change_and_suspended_is_retained(self):
        calls=[];api=types.SimpleNamespace(CreateProcessW=lambda *args:calls.append(args) or 1)
        proxy=h._DetachedCreation(api)
        args=('exe','mutable',None,None,False,h.original.CREATE_SUSPENDED|h.original.CREATE_NO_WINDOW,None,'cwd','startup','info')
        self.assertEqual(proxy.CreateProcessW(*args),1)
        self.assertEqual(calls[0][:5],args[:5]);self.assertEqual(calls[0][6:],args[6:])
        self.assertEqual(calls[0][5],h.original.CREATE_SUSPENDED|h.DETACHED_PROCESS)
        with self.assertRaises(RuntimeError):proxy.CreateProcessW(*[*args[:5],0,*args[6:]])

    def test_exact_source_args_kwargs_and_return_bytes_forwarded(self):
        calls=[];payload=b'invented\r\nsource\x00bytes'
        module=types.SimpleNamespace(check_output=lambda *a,**k:calls.append((a,k)) or payload)
        args=['git','show','HEAD:invented.py'];kwargs={'cwd':'invented','stderr':-2,'timeout':3}
        with patch.object(h,'sha',return_value=h.DIRECT_GIT_SHA):facade=h.GitFacade(module)
        self.assertIs(facade.check_output(args,**kwargs),payload)
        self.assertEqual(args,['git','show','HEAD:invented.py'])
        self.assertEqual(calls,[(([str(h.DIRECT_GIT),'show','HEAD:invented.py'],),dict(kwargs,creationflags=h.DETACHED_PROCESS))])

    def test_scoped_module_binding_restores_after_failure_without_global_patch(self):
        shared=types.SimpleNamespace(check_output=lambda *_:b'unchanged')
        module=types.SimpleNamespace(subprocess=shared);other=types.SimpleNamespace(subprocess=shared)
        with patch.object(h,'sha',return_value=h.DIRECT_GIT_SHA):
            with self.assertRaisesRegex(RuntimeError,'invented'):
                with h.scoped_git(module):
                    self.assertIs(other.subprocess,shared)
                    self.assertIs(module.subprocess._module,shared)
                    raise RuntimeError('invented')
        self.assertIs(module.subprocess,shared);self.assertIs(other.subprocess,shared)

    def test_non_git_shell_text_and_other_creation_flags_rejected(self):
        with patch.object(h,'sha',return_value=h.DIRECT_GIT_SHA):facade=h.GitFacade(types.SimpleNamespace())
        for args,kwargs in ((['git','push','origin'],{}),(['git','show','HEAD:x'],{'shell':True}),
            (['git','show','HEAD:x'],{'text':True}),(['git','show','HEAD:x'],{'creationflags':1})):
            with self.assertRaises(ValueError):facade.check_output(args,**kwargs)


if __name__=='__main__':unittest.main()
