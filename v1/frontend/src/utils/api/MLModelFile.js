import Model from './Model';

export default class MLModelFile extends Model {
  /** @inheritdoc */
  static get className() {
    return 'model';
  }

  /** @inheritdoc */
  _initProperties() {
    super._initProperties();

    this.filename = null;
    this.metadata_ = null;
    this.state = null;
  }

  get metadata() {
    return this.metadata_;
  }

  static async refresh() {
    let data = await this.backend().post(`${this.className}/refresh`);
    return data;
  }
}