/**
 * lariska.js is a micro-framework designed for rapid development of socket-based applications.
 * It features routing, templating, and state management, along with configurable payload options
 * for outgoing requests, streamlining the development of real-time, interactive applications.
 */

function Lariska({store, container, pages, url}) {

    if (!window.Handlebars) { throw new Error('Handlebars should be loaded to document'); }
    if (!window.io) { throw new Error('io from socketio should be loaded to document'); }
  
    this.store = store
    this.container = container // dom app locator
    this.pages = pages // all app pages
    this.handlers = {} // all handlers
    this.url = url
    this.socket = io.connect(this.url, {transports: ['websocket', 'polling']});
  
    this.render = function(template, container=null) {
  
            data = this.store
            if (!container) {container = this.container}
  
            console.log(`Rendering template ${template}  to ${container}`)
  
            try {
              const templateElement = document.querySelector(template);
  
              if (!templateElement) {
                throw new Error(`Template element ${template} not found`);
              }
  
  
              const outputElement = document.querySelector(container);
  
              if (!outputElement) {
                throw new Error('No element to put page into ');
              }
  
              var templateText = templateElement.innerHTML;
              var template = Handlebars.compile(templateText);
              var renderedHTML = template(data);
  
              outputElement.innerHTML = renderedHTML;
  
            } catch (error) {
              console.error(error);
            }
      }
  
  
    this.go = function (state) {
  
      if (this.pages[state]) {
        this.render("#"+state, this.container, this.store);
      } else {
        console.error(`State ${state} not found`);
      }
      this.state = state
    };
  
  
    this.payload = []
    this.addPayload = function(key){
       if (!this.store.hasOwnProperty(key)) {
          throw new Error(`Payload error: ${key} not in store`);
       } else {
          this.payload.push(key)
       }
    }
  
     this.emit = function(event, data={}){
       this.payload.forEach(key => data[key] = key in data ? data[key] : store[key]);
       this.socket.emit(event, data)
       console.log(`Socket event ${event} emitted`)
     }
  
     this.addHandler = function(name, func) {
         this.handlers[name] = func
         console.log(`Handler ${name} added`)
     }
  
     this.run = function(name, data) {
  
         if (typeof this.handlers[name] !== 'function') {
            throw new Error(`Handler with name ${name} doesn't exist.`);
        }
  
         console.log(`Handler ${name} running`)
         func = this.handlers[name](data)
     }
  
     this.on = function(event, frame=null, callback=null, container=null){
  
  
        this.socket.on(event, (data) => {
  
          console.log(`Socket event ${event} received`)
          console.log(data)
  
           if (callback) { callback(data) }
           if (frame) {
               this.render(frame, container)
           }
        })
     }
  }
  