import {describe,it,expect} from 'vitest';import{calculateScheduleStatus}from'./schedule';
describe('schedule rules',()=>{it('flags overdue incomplete projects',()=>expect(calculateScheduleStatus(50,'2026-01-01','2026-03-01',15,new Date('2026-04-01'))).toBe('Delayed'));it('returns insufficient data',()=>expect(calculateScheduleStatus(50,null,'2026-03-01')).toBe('Insufficient Data'))});
