export default class Model {
  constructor(data) {
    this._init_properties();
    Object.assign(this, data || {});
  }

  /** @inheritdoc */
  _init_properties() {
    this.id = null;
  }

  /** A method that applys Object.assign but selectively to update only existing properties if they have a matching key in data */
  _assign_data(data, strict=false) {
    if (strict) {
      for (let key in data) {
        if (this.hasOwnProperty(key)) {
          this[key] = data[key];
        }
      }
    } else {
      Object.assign(this, data);
    }
  }
}