import sleuth

import fakemodule


sleuth.tap(fakemodule.doNothing, sleuth.callOnEnter,
           callback=fakemodule.doNothing_callback)
sleuth.tap(fakemodule.returnValue, sleuth.callOnResult,
           compare=lambda x: x==1, callback=fakemodule.returnValue_callback)
