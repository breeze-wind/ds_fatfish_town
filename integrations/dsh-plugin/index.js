import Schema from '@deepseek-ai/schemastery'
import { defineTool } from '@deepseek-ai/dsh-tools'
import { createHabitatClient } from './api-client.js'

export const name = 'cyber-habitat-dsh-plugin'
export const inject = ['tools']

export const Config = Schema.object({
  baseUrl: Schema.string().default('http://127.0.0.1:8765'),
})

function jsonOutput() {
  return {
    schema: { type: 'string' },
    render: (_args, value) => [{ type: 'text', text: value }],
  }
}

export function apply(ctx, config) {
  const client = createHabitatClient(config.baseUrl)

  ctx.tools.register(defineTool({
    name: 'habitat_list_residents',
    description: 'List residents and their current energy, safety, and growth in Cyber Habitat.',
    parameters: {},
    output: jsonOutput(),
    timeoutMs: 15_000,
    async execute(_args, exec) {
      return JSON.stringify(await client.listResidents(exec.signal))
    },
  }))

  ctx.tools.register(defineTool({
    name: 'habitat_recent_events',
    description: 'Read recent events from the Cyber Habitat world event log.',
    parameters: {
      limit: { type: 'number', required: true, description: 'Number of events to read, from 1 to 100.' },
    },
    output: jsonOutput(),
    timeoutMs: 15_000,
    async execute(args, exec) {
      const limit = args.limit
      return JSON.stringify(await client.recentEvents(limit, exec.signal))
    },
  }))

  ctx.tools.register(defineTool({
    name: 'habitat_submit_action',
    description: 'Submit a resident action to Cyber Habitat. The World Director validates every action and may block it.',
    parameters: {
      resident_id: { type: 'string', required: true, description: 'The resident id returned by habitat_list_residents.' },
      kind: { type: 'string', required: true, description: 'Action kind: rest, learn, socialize, or attack.' },
    },
    output: jsonOutput(),
    timeoutMs: 15_000,
    async execute(args, exec) {
      const response = await client.submitAction(args.resident_id, args.kind, exec.signal)
      return JSON.stringify(response)
    },
  }))
}
