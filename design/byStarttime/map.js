function (doc) {
  if (doc.type == "annotation") {
    emit(doc.starttime, doc);
  }
}

