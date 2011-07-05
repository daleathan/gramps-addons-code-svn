register(GRAMPLET, 
         id="Face Detection", 
         name=_("Face Detection"), 
         description = _("Gramplet for detecting and assigning faces"),
         version = '1.0.5',
         gramps_target_version="3.3",
         status = STABLE,
         fname="FaceDetection.py",
         height=200,
         gramplet = 'FaceDetection',
         gramplet_title=_("Faces"),
         navtypes=["Media"],
         )
