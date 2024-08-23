import axios from "@/utils/axios";

export default class BaseService {
  /**
   * Abstract getter for resource path prefix.
   * @returns {string} Resource path prefix.
   */
  get resource_prefix() {
    throw new Error("Method 'resource_prefix' must be implemented.");
  }

  /**
   * Abstract getter for model class.
   * @returns {Model} Model class.  
   */
  get model_class() {
    throw new Error("Method 'model_class' must be implemented.");
  }

  // -- accessors for path name fetch, update, create, delete API endpoints
  fetch_path() {
    return `/${this.resource_prefix}/${id}`;
  }

  update_path(id) {
    return this.fetch_path(id);
  }

  create_path() {
    return `/${this.resource_prefix}`;
  }

  delete_path(id) {
    return this.fetch_path(id);
  }

  // --- default methods

  /**
   * Fetch a single resource by id.
   * @param {F} config Axios config for the request.
   * @returns An instance of the resource model class.
   * @throws {Error} If the request fails (e.g. because it does not exist).
   */
  async fetch(config={}) {
    let {data} = await axios.get(this.fetch_path(), config);
    return new this.model_class(data);
  }

  /** 
   * Create a single resource.
   * @param {Object} data Data to create the resource.
   * @param {Object} config Axios config for the request.
   * @returns An instance of the create resource model class on success.
   * @throws {Error} If the request fails.
   */
  async create(model, config={}) {
    let {data} = await axios.post(this.create_path(), model, config);
    return new this.model_class(data);
  }

  /**
   * Update a single resource by id.
   * @param {*} id Identifier of the resource to update.
   * @param {*} data Data to update the resource.
   * @param {*} config Axios config for the request.
   * @returns An instance of the updated resource model class on success.
   * @throws {Error} If the request fails.
   */
  async update(id, model, config={}) {
    let {data} = await axios.put(this.update_path(id), model, config);
    return new this.model_class(data);
  }

  /**
   * Delete a single resource by id.
   * @param {*} id Identifier of the resource to delete.
   * @param {*} config Axios config for the request.
   * @returns An instance of the deleted resource model class on success.
   * @throws {Error} If the request fails.
   */
  async delete(id, config={}) {
    await axios.delete(this.delete_path(id), config);
    return true;
  }

}