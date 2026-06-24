import "fake-indexeddb/auto";
import fetch, { Headers, Request, Response } from 'node-fetch';
import { TextEncoder, TextDecoder } from 'util';
import { webcrypto } from 'crypto';
import { serialize, deserialize } from 'v8';

// Global polyfills for Jest environment
if (typeof global.fetch === 'undefined') {
  (global as any).fetch = fetch;
}
if (typeof global.Request === 'undefined') {
  (global as any).Request = Request;
}
if (typeof global.Response === 'undefined') {
  (global as any).Response = Response;
}
if (typeof global.Headers === 'undefined') {
  (global as any).Headers = Headers;
}
if (typeof global.TextEncoder === 'undefined') {
  (global as any).TextEncoder = TextEncoder;
}
if (typeof global.TextDecoder === 'undefined') {
  (global as any).TextDecoder = TextDecoder;
}
if (typeof (global as any).crypto === 'undefined' || !(global as any).crypto.subtle) {
  Object.defineProperty(global, 'crypto', {
    value: webcrypto,
    writable: true,
    configurable: true
  });
}
if (typeof (global as any).structuredClone !== 'function') {
  (global as any).structuredClone = (val: any) => deserialize(serialize(val));
}